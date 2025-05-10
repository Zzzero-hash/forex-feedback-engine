import time
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd

# Attempt optional import of pandas_ta for indicators
try:
    import pandas_ta as ta  # type: ignore
    TA_AVAILABLE = True
except ImportError:
    ta = None
    TA_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("pandas_ta not installed; advanced indicators and pattern detection disabled.")

logger = logging.getLogger(__name__)

class HistoricalDataCollector:
    """
    Manages historical price data collection and processing for temporal context.
    Works with both Polygon API for real data and provides fallback simulation.
    """
    def __init__(self, data_feed=None, lookback_periods: int = 60, timeframe_minutes: int = 5):
        """
        Initialize the historical data collector.
        
        Args:
            data_feed: DataFeed instance with Polygon client
            lookback_periods: Number of candles to collect per symbol
            timeframe_minutes: Timeframe in minutes for each candle
        """
        self.data_feed = data_feed
        self.lookback_periods = lookback_periods
        self.timeframe_minutes = timeframe_minutes
        self.historical_data = {}  # symbol -> dataframe mapping
        self.last_update_time = {}  # symbol -> last update timestamp
        
        # Update frequency in seconds (default: 5 min)
        self.update_frequency = self.timeframe_minutes * 60
        
        logger.info(f"HistoricalDataCollector initialized with lookback_periods={lookback_periods}, "
                   f"timeframe_minutes={timeframe_minutes}")
    
    def _fetch_historical_data_from_polygon(self, symbol: str) -> Optional[pd.DataFrame]:
        """Fetch historical price data from Polygon API."""
        if not self.data_feed or not self.data_feed.client:
            logger.warning("No Polygon client available for historical data")
            return None
            
        try:
            now = datetime.now()
            
            # Check if the symbol is crypto (trades 24/7) or forex (weekday trading)
            is_crypto = self.data_feed.detect_symbol_type(symbol) == 'crypto'
            is_weekend = now.weekday() >= 5  # 5=Saturday, 6=Sunday
            
            # For crypto, we can use more recent data on any day since it trades 24/7
            # For forex on weekends, we need to use data from previous trading day
            if is_crypto:
                # Crypto: use recent data (yesterday to ensure complete bars)
                end_datetime = now - timedelta(hours=1)  # 1 hour ago to ensure complete data
                start_datetime = end_datetime - timedelta(days=3)  # 3 days of data
                logger.info(f"Using crypto historical data for {symbol} (trades 24/7)")
            elif is_weekend:
                # Forex on weekend: use Friday's data
                days_to_friday = (now.weekday() - 4) % 7  # 5->1, 6->2 days back to Friday
                end_datetime = now - timedelta(days=days_to_friday, hours=1)  # Friday - safety margin
                start_datetime = end_datetime - timedelta(days=5)  # 5 days before that
                logger.info(f"Weekend detected for forex {symbol}. Using data from {start_datetime.strftime('%Y-%m-%d')} to {end_datetime.strftime('%Y-%m-%d')}")
            else:
                # Normal weekday for forex
                end_datetime = now - timedelta(hours=1)  # 1 hour ago to ensure complete data
                start_datetime = end_datetime - timedelta(days=5)  # 5 days of data
                logger.info(f"Using weekday forex historical data for {symbol}")
            
            # Convert to string format YYYY-MM-DD that Polygon expects
            end_date_str = end_datetime.strftime('%Y-%m-%d')
            start_date_str = start_datetime.strftime('%Y-%m-%d')
            
            # Get proper ticker format for the symbol
            polygon_symbol = self.data_feed.get_polygon_ticker(symbol)
            
            logger.info(f"Fetching historical data for {symbol} as {polygon_symbol} from {start_date_str} to {end_date_str}")
            
            # Call Polygon API for aggregated data using proper date strings
            bars = self.data_feed.client.get_aggs(
                ticker=polygon_symbol,
                multiplier=self.timeframe_minutes,
                timespan="minute",
                from_=start_date_str,  # Use the string date format for better reliability
                to=end_date_str,       # Use the string date format for better reliability
                limit=self.lookback_periods
            )
            
            if not bars or len(bars) == 0:
                logger.warning(f"No historical data available for {symbol} ({polygon_symbol})")
                return None
                
            # Convert to DataFrame
            data = []
            for bar in bars:
                data.append({
                    'timestamp': datetime.fromtimestamp(bar.timestamp / 1000),
                    'open': bar.open,
                    'high': bar.high,
                    'low': bar.low,
                    'close': bar.close,
                    'volume': bar.volume,
                    'vwap': getattr(bar, 'vwap', None)  # Some markets may not have VWAP
                })
            
            df = pd.DataFrame(data)
            logger.info(f"Successfully fetched {len(df)} historical bars for {symbol} ({polygon_symbol})")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}", exc_info=True)
            return None
    
    def _generate_simulated_data(self, symbol: str) -> pd.DataFrame:
        """Generate simulated historical price data when real data is unavailable."""
        logger.info(f"Generating simulated historical data for {symbol}")
        
        # Get current price if available, otherwise use default
        current_price = 1.0
        if self.data_feed:
            try:
                quote = self.data_feed.get_quote(symbol)
                if quote and 'price' in quote:
                    current_price = quote['price']
            except Exception as e:
                logger.warning(f"Error getting current price for {symbol}: {e}")
        
        # Generate timestamps for the lookback period
        end_time = datetime.now()
        timestamps = [end_time - timedelta(minutes=i * self.timeframe_minutes) 
                     for i in range(self.lookback_periods)]
        timestamps.reverse()  # Oldest first
        
        # Generate price series with realistic patterns
        # Start from current and work backwards with reasonable volatility
        price_close = [current_price]
        volatility = current_price * 0.0005  # 0.05% volatility per candle
        
        for i in range(1, self.lookback_periods):
            # Introduce some trends and patterns
            trend = 0
            # Create a short trend every 10-15 candles
            if i % 15 < 7:
                trend = volatility * 0.8
            elif i % 10 < 5:
                trend = -volatility * 0.8
                
            # Add random movement + trend
            new_price = price_close[-1] + np.random.normal(-trend, volatility)
            price_close.append(new_price)
            
        price_close.reverse()  # Match timestamps order
        
        # Generate OHLC values based on close prices
        data = []
        for i, close in enumerate(price_close):
            candle_volatility = close * 0.0003  # 0.03% intra-candle volatility
            high = close + abs(np.random.normal(0, candle_volatility))
            low = close - abs(np.random.normal(0, candle_volatility))
            open_price = low + (high - low) * np.random.random()
            
            # Simulate volume (just for completeness)
            volume = np.random.randint(50, 500)
            
            data.append({
                'timestamp': timestamps[i],
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume,
                'vwap': close  # Simplified VWAP as just the close price
            })
        
        return pd.DataFrame(data)
    
    def get_historical_data(self, symbol: str, force_refresh: bool = False) -> pd.DataFrame:
        """
        Get historical data for a symbol, updating if necessary.
        
        Args:
            symbol: The currency pair symbol (e.g., 'EURUSD')
            force_refresh: Whether to force refresh the data regardless of cache
            
        Returns:
            DataFrame with OHLCV data
        """
        current_time = time.time()
        
        # Check if we need to update the data
        if (symbol not in self.historical_data or 
            symbol not in self.last_update_time or
            current_time - self.last_update_time.get(symbol, 0) > self.update_frequency or
            force_refresh):
            
            # Try to fetch real data first
            df = self._fetch_historical_data_from_polygon(symbol)
            
            # If real data is unavailable, use simulated data as fallback
            if df is None or df.empty:
                logger.warning(f"No historical data available for {symbol} from API. Using simulated data.")
                df = self._generate_simulated_data(symbol)
                logger.info(f"Generated simulated data for {symbol} with {len(df)} candles")

            # Store the data
            self.historical_data[symbol] = df
            self.last_update_time[symbol] = current_time
            
            logger.debug(f"Updated historical data for {symbol} ({len(df)} rows)")
        
        return self.historical_data.get(symbol, pd.DataFrame())
    
    def calculate_technical_indicators(self, symbol: str) -> Dict[str, Any]:
        """
        Calculate technical indicators for a symbol based on historical data.
        
        Args:
            symbol: The currency pair symbol
            
        Returns:
            Dictionary containing calculated technical indicators
        """
        df = self.get_historical_data(symbol)
        results: Dict[str, Any] = {}
        
        # Check if we have sufficient data
        if df is None or df.empty or len(df) < 5:
            logger.warning(f"Not enough historical data for {symbol} to calculate indicators (min 5 candles needed)")
            # Return default values for essential fields to prevent errors downstream
            return {
                'price_current': 0.0,
                'price_open': 0.0,
                'price_high': 0.0, 
                'price_low': 0.0,
                'change_1candle_pct': 0.0,
                'trend_direction': 'neutral'
            }
        
        try:
            # Basic price information from close
            results['price_current'] = float(df['close'].iloc[-1])
            results['price_open'] = float(df['open'].iloc[-1])
            results['price_high'] = float(df['high'].iloc[-1])
            results['price_low'] = float(df['low'].iloc[-1])
            
            # Recent performance - safely calculate percentage changes
            if len(df) >= 2 and df['close'].iloc[-2] != 0:
                results['change_1candle_pct'] = float((df['close'].iloc[-1] / df['close'].iloc[-2] - 1) * 100)
            else:
                results['change_1candle_pct'] = 0.0
                
            if len(df) >= 5 and df['close'].iloc[-5] != 0:
                results['change_5candle_pct'] = float((df['close'].iloc[-1] / df['close'].iloc[-5] - 1) * 100)
            else:
                results['change_5candle_pct'] = 0.0
            
            # Advanced indicators via pandas_ta if available
            if TA_AVAILABLE:
                try:
                    if len(df) >= 14:
                        results['ema_14'] = float(ta.ema(df['close'], length=14).iloc[-1])
                    if len(df) >= 50:
                        results['ema_50'] = float(ta.ema(df['close'], length=50).iloc[-1])
                    if len(df) >= 26:  # MACD needs at least 26 periods
                        macd = ta.macd(df['close'])
                        results['macd_hist'] = float(macd['MACDh_12_26_9'].iloc[-1])
                    if len(df) >= 14:
                        results['atr_14'] = float(ta.atr(df['high'], df['low'], df['close'], length=14).iloc[-1])
                except Exception as e:
                    logger.warning(f"pandas_ta failed to calculate some indicators for {symbol}: {e}")
                
                # Price vs EMAs - safely calculate percentages
                if 'ema_14' in results and results['ema_14'] > 0:
                    results['price_to_ema14_pct'] = float((results['price_current'] / results['ema_14'] - 1) * 100)
                if 'ema_50' in results and results['ema_50'] > 0:
                    results['price_to_ema50_pct'] = float((results['price_current'] / results['ema_50'] - 1) * 100)
                
                try:
                    if len(df) >= 14:
                        results['rsi_14'] = float(ta.rsi(df['close'], length=14).iloc[-1])
                except Exception as e:
                    logger.warning(f"pandas_ta failed to calculate RSI for {symbol}: {e}")
            
            # Volatility (as percentage of price via standard deviation) - safely calculate
            if len(df) >= 10 and results['price_current'] > 0:
                price_std = df['close'].rolling(window=10).std().iloc[-1]
                results['volatility_10_pct'] = float(price_std / results['price_current'] * 100)
            else:
                results['volatility_10_pct'] = 0.0
            
            # Trend direction based on multiple timeframes
            if len(df) >= 20:
                results['trend_direction'] = self._determine_trend(df)
            else:
                results['trend_direction'] = 'neutral'
                
        except Exception as e:
            logger.error(f"Error calculating indicators for {symbol}: {e}", exc_info=True)
            # Default values if calculation fails
            if 'price_current' not in results:
                results['price_current'] = 0.0
            if 'trend_direction' not in results:
                results['trend_direction'] = 'neutral'
        
        return results
    
    def _determine_trend(self, df: pd.DataFrame) -> str:
        """Determine the trend direction based on multiple indicators."""
        # Check for valid dataframe with sufficient data
        if df is None or df.empty or len(df) < 5:
            return "neutral"
            
        # Check for NaN or zero values
        if df['close'].isna().any() or (df['close'] == 0).any():
            logger.warning("NaN or zero values found in price data, trend analysis may be unreliable")
        
        try:
            # Check short-term trend (5 candles)
            short_trend = "neutral"
            if len(df) >= 5:
                if df['close'].iloc[-1] > df['close'].iloc[-5]:
                    short_trend = "bullish"
                elif df['close'].iloc[-1] < df['close'].iloc[-5]:
                    short_trend = "bearish"
            
            # Check medium-term trend (20 candles)
            medium_trend = "neutral"
            if len(df) >= 20:
                if df['close'].iloc[-1] > df['close'].iloc[-20]:
                    medium_trend = "bullish"
                elif df['close'].iloc[-1] < df['close'].iloc[-20]:
                    medium_trend = "bearish"
            
            # MA crossover
            ma_trend = "neutral"
            if len(df) >= 50:
                # Calculate moving averages, handling NaN values
                ma_short = df['close'].rolling(window=20).mean()
                ma_long = df['close'].rolling(window=50).mean()
                
                # Only proceed if we have valid values
                if not pd.isna(ma_short.iloc[-1]) and not pd.isna(ma_long.iloc[-1]) and \
                   not pd.isna(ma_short.iloc[-2]) and not pd.isna(ma_long.iloc[-2]):
                    
                    if ma_short.iloc[-1] > ma_long.iloc[-1] and ma_short.iloc[-2] <= ma_long.iloc[-2]:
                        ma_trend = "bullish_crossover"
                    elif ma_short.iloc[-1] < ma_long.iloc[-1] and ma_short.iloc[-2] >= ma_long.iloc[-2]:
                        ma_trend = "bearish_crossover"
                    elif ma_short.iloc[-1] > ma_long.iloc[-1]:
                        ma_trend = "bullish"
                    elif ma_short.iloc[-1] < ma_long.iloc[-1]:
                        ma_trend = "bearish"
            
            # Combine the trends to get an overall picture
            # If 2 out of 3 agree, use that direction
            trends = [short_trend, medium_trend, ma_trend]
            bullish_count = trends.count("bullish") + trends.count("bullish_crossover")
            bearish_count = trends.count("bearish") + trends.count("bearish_crossover")
            
            if bullish_count >= 2:
                return "bullish" if "bullish_crossover" not in trends else "bullish_crossover"
            elif bearish_count >= 2:
                return "bearish" if "bearish_crossover" not in trends else "bearish_crossover"
            else:
                return "neutral"
                
        except Exception as e:
            logger.error(f"Error determining trend: {e}", exc_info=True)
            return "neutral"
    
    def get_price_chart_ascii(self, symbol: str, bars: int = 20) -> str:
        """
        Generate an ASCII chart representation of price movements.
        
        Args:
            symbol: The currency pair symbol
            bars: Number of bars to include (default: 20)
            
        Returns:
            ASCII chart as a string
        """
        df = self.get_historical_data(symbol)
        
        # Handle empty dataframes
        if df is None or df.empty or len(df) < 5:
            logger.warning(f"Insufficient data for ASCII chart for {symbol}")
            return "Insufficient data for chart\n[No price history available]"
        
        try:
            # Limit to the requested number of bars
            df_subset = df.tail(min(bars, len(df)))
            
            # Check for zero or invalid prices
            if (df_subset['low'].isna().any() or 
                df_subset['high'].isna().any() or 
                (df_subset['low'] == 0).all() or 
                (df_subset['high'] == 0).all()):
                
                logger.warning(f"Invalid prices detected for {symbol}, cannot generate chart")
                return f"Cannot generate chart for {symbol}\n[Invalid price data detected]"
            
            # Get min and max values for scaling, handling potential zeros
            min_val = df_subset['low'].min()
            max_val = df_subset['high'].max()
            
            # Add small buffer to prevent min=max condition
            if min_val == max_val:
                if min_val == 0:
                    # If both are zero, use dummy values
                    min_val = 0.95
                    max_val = 1.05
                else:
                    # Add a 5% buffer around the value
                    buffer = abs(min_val) * 0.05
                    min_val -= buffer
                    max_val += buffer
            
            # Chart height
            height = 10
            
            # Scale factor
            scale = height / (max_val - min_val)
            
            # Generate chart
            chart = []
            chart.append(f"Price chart for {symbol} (Last {len(df_subset)} {self.timeframe_minutes}-min candles)")
            chart.append(f"High: {max_val:.5f} | Low: {min_val:.5f}")
            chart.append("-" * (len(df_subset) + 2))
            
            # Create Y-axis and plot
            for y in range(height, -1, -1):
                price_level = min_val + (y / scale)
                line = f"{price_level:.5f} |"
                
                for i, row in df_subset.iterrows():
                    # Verify row values are valid
                    if pd.isna(row['open']) or pd.isna(row['close']) or pd.isna(row['high']) or pd.isna(row['low']):
                        line += " "
                        continue
                    
                    # Determine candle body
                    if row['close'] >= row['open']:
                        # Bullish candle
                        body_top = row['close']
                        body_bottom = row['open']
                        candle_char = "█"
                    else:
                        # Bearish candle
                        body_top = row['open']
                        body_bottom = row['close']
                        candle_char = "▒"
                    
                    # Determine if this price level is part of the candle
                    price_in_wick = min_val <= price_level <= max_val and (
                        (price_level <= row['high'] and price_level >= body_top) or
                        (price_level >= row['low'] and price_level <= body_bottom)
                    )
                    
                    price_in_body = min_val <= price_level <= max_val and (
                        price_level <= body_top and price_level >= body_bottom
                    )
                    
                    if price_in_body:
                        line += candle_char
                    elif price_in_wick:
                        line += "|"
                    else:
                        line += " "
                
                chart.append(line)
            
            # Add time axis with proper validation
            times = []
            for i, timestamp in enumerate(df_subset['timestamp']):
                if pd.isna(timestamp):
                    times.append("")
                    continue
                    
                if i == 0 or i == len(df_subset) - 1 or i % 5 == 0:
                    try:
                        times.append(timestamp.strftime("%H:%M"))
                    except Exception:
                        times.append("??:??")
                else:
                    times.append("")
            
            chart.append("-" * (len(df_subset) + 2))
            
            # Format time axis to fit under the chart
            time_axis = "     |"
            for t in times:
                if t:
                    # Make sure it fits in the column by truncating if needed
                    time_axis += t[:1]
                else:
                    time_axis += " "
            chart.append(time_axis)
            
            return "\n".join(chart)
            
        except Exception as e:
            logger.error(f"Error generating ASCII chart for {symbol}: {e}", exc_info=True)
            return f"Error generating chart: {str(e)}"
    
    def get_pattern_analysis(self, symbol: str) -> Dict[str, Any]:
        """
        Analyze price patterns and formations.
        
        Args:
            symbol: The currency pair symbol
            
        Returns:
            Dictionary containing identified patterns
        """
        df = self.get_historical_data(symbol)
        results = {"patterns": []}
        
        # Check if dataframe is empty or insufficient data
        if df is None or df.empty or len(df) < 20:
            logger.warning(f"Insufficient historical data for {symbol} to detect patterns (min 20 candles needed)")
            return results
        
        patterns = []
        
        try:
            latest = df.iloc[-1]  # Current candle for volume analysis and reference
            
            # Candlestick patterns via pandas_ta if available
            if TA_AVAILABLE:
                o, h, l, c = df['open'], df['high'], df['low'], df['close']
                
                try:
                    pattern_funcs = {
                        'doji': ta.cdl_doji,
                        'hammer': ta.cdl_hammer,
                        'shooting_star': ta.cdl_shooting_star,
                        'bullish_engulfing': ta.cdl_engulfing,
                        'bearish_engulfing': ta.cdl_engulfing
                    }
                    
                    for name, func in pattern_funcs.items():
                        try:
                            val = func(o, h, l, c).iloc[-1]
                            if name == 'bullish_engulfing' and val > 0:
                                patterns.append(name)
                            elif name == 'bearish_engulfing' and val < 0:
                                patterns.append(name)
                            elif name in ['doji', 'hammer', 'shooting_star'] and val != 0:
                                patterns.append(name)
                        except Exception as e:
                            logger.warning(f"Failed to detect pattern {name} for {symbol}: {str(e)}")
                except Exception as e:
                    logger.warning(f"Error in candlestick pattern detection for {symbol}: {str(e)}")
            
            # Add strength indication based on volume (if available)
            if 'volume' in df.columns and not df['volume'].isnull().all():
                try:
                    avg_volume = df['volume'].rolling(window=10).mean().iloc[-1]
                    if latest['volume'] > 1.5 * avg_volume:
                        results['volume_signal'] = "strong"
                    elif latest['volume'] < 0.5 * avg_volume:
                        results['volume_signal'] = "weak"
                    else:
                        results['volume_signal'] = "average"
                except Exception as e:
                    logger.warning(f"Error calculating volume signal for {symbol}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error in pattern analysis for {symbol}: {str(e)}", exc_info=True)
        
        results["patterns"] = patterns
        return results

# Example usage (for reference):
# data_feed = DataFeed(api_key="your_polygon_api_key")
# historical_collector = HistoricalDataCollector(data_feed)
# data = historical_collector.get_historical_data("EURUSD")
# indicators = historical_collector.calculate_technical_indicators("EURUSD")
# chart = historical_collector.get_price_chart_ascii("EURUSD")
