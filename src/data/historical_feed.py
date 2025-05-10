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
            # Calculate time range for historical data
            end_ts = int(time.time() * 1000)
            # Calculate start time based on lookback periods and timeframe
            start_ts = int((time.time() - (self.lookback_periods * self.timeframe_minutes * 60)) * 1000)
            
            # Convert symbol format for Polygon (e.g., EURUSD -> C:EURUSD)
            polygon_symbol = f"C:{symbol}"
            
            logger.info(f"Fetching historical data for {symbol} from {datetime.fromtimestamp(start_ts/1000)} "
                       f"to {datetime.fromtimestamp(end_ts/1000)}")
            
            # Call Polygon API for aggregated data
            bars = self.data_feed.client.get_aggs(
                ticker=polygon_symbol,
                multiplier=self.timeframe_minutes,
                timespan="minute",
                from_=start_ts,
                to=end_ts,
                limit=self.lookback_periods
            )
            
            if not bars or len(bars) == 0:
                logger.warning(f"No historical data available for {symbol}")
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
            logger.info(f"Successfully fetched {len(df)} historical bars for {symbol}")
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
            # Require real data; no simulation fallback
            if df is None:
                logger.error(f"Historical data unavailable for {symbol}. Ensure Polygon API returns data.")
                df = pd.DataFrame()  # empty DataFrame to prevent further errors

            # Store the data
            self.historical_data[symbol] = df
            self.last_update_time[symbol] = current_time
            
            logger.debug(f"Updated historical data for {symbol} ({len(df)} rows)")
        
        return self.historical_data[symbol]
    
    def calculate_technical_indicators(self, symbol: str) -> Dict[str, Any]:
        """
        Calculate technical indicators for a symbol based on historical data.
        
        Args:
            symbol: The currency pair symbol
            
        Returns:
            Dictionary containing calculated technical indicators
        """
        df = self.get_historical_data(symbol)
        if len(df) < 5:  # Need at least 5 candles for basic indicators
            logger.warning(f"Not enough historical data for {symbol} to calculate indicators")
            return {}
        
        results: Dict[str, Any] = {}
        
        # Basic price information from close
        results['price_current'] = float(df['close'].iloc[-1])
        results['price_open'] = float(df['open'].iloc[-1])
        results['price_high'] = float(df['high'].iloc[-1])
        results['price_low'] = float(df['low'].iloc[-1])
        
        # Recent performance
        results['change_1candle_pct'] = float((df['close'].iloc[-1] / df['close'].iloc[-2] - 1) * 100)
        
        if len(df) >= 5:
            results['change_5candle_pct'] = float((df['close'].iloc[-1] / df['close'].iloc[-5] - 1) * 100)
        
        # Advanced indicators via pandas_ta if available
        if TA_AVAILABLE:
            try:
                results['ema_14'] = float(ta.ema(df['close'], length=14).iloc[-1])
                results['ema_50'] = float(ta.ema(df['close'], length=50).iloc[-1])
                macd = ta.macd(df['close'])
                results['macd_hist'] = float(macd['MACDh_12_26_9'].iloc[-1])
                results['atr_14'] = float(ta.atr(df['high'], df['low'], df['close'], length=14).iloc[-1])
            except Exception:
                logger.warning(f"pandas_ta failed to calculate some indicators for {symbol}")
            # Price vs EMAs
            if 'ema_14' in results:
                results['price_to_ema14_pct'] = float((results['price_current'] / results['ema_14'] - 1) * 100)
            if 'ema_50' in results:
                results['price_to_ema50_pct'] = float((results['price_current'] / results['ema_50'] - 1) * 100)
            try:
                results['rsi_14'] = float(ta.rsi(df['close'], length=14).iloc[-1])
            except Exception:
                logger.warning(f"pandas_ta failed to calculate RSI for {symbol}")
        
        # Fallback or additional indicators here (existing code continues)
        # Volatility (as percentage of price via standard deviation)
        if len(df) >= 10:
            price_std = df['close'].rolling(window=10).std().iloc[-1]
            results['volatility_10_pct'] = float(price_std / results['price_current'] * 100)

        # Trend direction based on multiple timeframes
        if len(df) >= 20:
            results['trend_direction'] = self._determine_trend(df)
        
        return results
    
    def _determine_trend(self, df: pd.DataFrame) -> str:
        """Determine the trend direction based on multiple indicators."""
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
            ma_short = df['close'].rolling(window=20).mean()
            ma_long = df['close'].rolling(window=50).mean()
            
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
        if len(df) < 5:
            return "Insufficient data for chart"
        
        # Limit to the requested number of bars
        df_subset = df.tail(min(bars, len(df)))
        
        # Get min and max values for scaling
        min_val = df_subset['low'].min()
        max_val = df_subset['high'].max()
        
        # Chart height
        height = 10
        
        # Scale factor
        scale = height / (max_val - min_val) if max_val != min_val else 1
        
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
        
        # Add time axis
        times = []
        for i, timestamp in enumerate(df_subset['timestamp']):
            if i == 0 or i == len(df_subset) - 1 or i % 5 == 0:
                times.append(timestamp.strftime("%H:%M"))
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
    
    def get_pattern_analysis(self, symbol: str) -> Dict[str, Any]:
        """
        Analyze price patterns and formations.
        
        Args:
            symbol: The currency pair symbol
            
        Returns:
            Dictionary containing identified patterns
        """
        df = self.get_historical_data(symbol)
        if len(df) < 20:
            return {"patterns": []}
        
        patterns = []
        results = {"patterns": patterns}
        latest = df.iloc[-1]  # Current candle for volume analysis and reference
        
        # Candlestick patterns via pandas_ta if available
        if TA_AVAILABLE:
            o, h, l, c = df['open'], df['high'], df['low'], df['close']
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
                except Exception:
                    logger.warning(f"pandas_ta failed to detect pattern {name} for {symbol}")
        
        # Add strength indication based on volume (if available)
        if 'volume' in df.columns and not df['volume'].isnull().all():
            avg_volume = df['volume'].rolling(window=10).mean().iloc[-1]
            if latest['volume'] > 1.5 * avg_volume:
                results['volume_signal'] = "strong"
            elif latest['volume'] < 0.5 * avg_volume:
                results['volume_signal'] = "weak"
            else:
                results['volume_signal'] = "average"
        
        return results

# Example usage (for reference):
# data_feed = DataFeed(api_key="your_polygon_api_key")
# historical_collector = HistoricalDataCollector(data_feed)
# data = historical_collector.get_historical_data("EURUSD")
# indicators = historical_collector.calculate_technical_indicators("EURUSD")
# chart = historical_collector.get_price_chart_ascii("EURUSD")
