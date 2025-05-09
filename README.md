# Feedback Loop Trading System

This project is a feedback-loop driven trading system designed for binary options trading. It integrates real-time market data sources, uses an LLM-based decision engine with configurable risk management, and features enhanced market analysis with technical indicators for better pair selection.

## Features

- Signal-Only Mode: System generates trading signals without executing real trades
- OpenAI Integration: Uses o4-mini LLM model to make trading decisions
- Enhanced Pair Selection: Uses real-time market data and technical indicators for better trading pair selection
- Technical Analysis: Calculates RSI, volatility, momentum and price changes for more informed decisions
- Risk Management: Configurable profit targets and loss limits
- Trade History: Records trades for analysis and model feedback

## Recent Enhancements

1. Updated LLM Model: Changed from "gpt-3.5-turbo" to "o4-mini" for improved performance
2. Signal-Only Mode: System now operates in signal-only mode, generating trading signals without executing real trades
3. Enhanced Trading Pair Selection: Improved algorithm now uses real-time market data and technical indicators
4. Expanded Forex Pairs: Updated to include a comprehensive list of 28 major and minor forex pairs

## Technical Indicators

The system now analyzes multiple technical indicators to select the optimal trading pair:

- RSI (Relative Strength Index): Measures the momentum of price movements
- Volatility: Calculates standard deviation of price changes
- Momentum: Tracks the rate of price changes over time
- Price Change Percentage: Monitors recent price movements
