# MCP Bybit Trader
[![smithery badge](https://smithery.ai/badge/@dlwjdtn535/bybit-trader)](https://smithery.ai/server/@dlwjdtn535/bybit-trader)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-support-yellow.svg)](https://buymeacoffee.com/dlwjdtn535)

A powerful MCP (Model-Controller-Prompt) based trading bot for Bybit cryptocurrency exchange that provides various trading functionalities and backtesting capabilities.

## Features

### Market Data
- Real-time orderbook data retrieval
- K-line (candlestick) data with customizable intervals
- Advanced technical indicators using TA-Lib
  - Moving Averages (SMA, EMA)
  - RSI (Relative Strength Index)
  - MACD (Moving Average Convergence Divergence)
  - Bollinger Bands
  - Stochastic Oscillator
  - ATR (Average True Range)
  - OBV (On Balance Volume)
  - And more...
- Ticker information
- Exchange instrument details

### Trading Operations
- Place market and limit orders
- Support for spot and futures trading
- Advanced order types (TP/SL, trailing stop)
- Position management
- Margin mode configuration
- Leverage settings
- Order history tracking
- Open order monitoring

### Account Management
- Wallet balance checking
- Position information
- API key information
- Multiple account types support (UNIFIED, CONTRACT, SPOT)

### Backtesting
- Historical data-based strategy testing
- Customizable technical indicators
- Position size management
- Profit target and stop loss settings
- Performance metrics calculation
- Detailed trade history

## API Key Setup

To use this trading bot, you need to create an API key from Bybit. Follow these important steps:

1. Go to Bybit and log into your account
2. Navigate to API Management
3. Create a new API key
4. **Important Security Settings:**
   - Enable IP restriction
   - Add ONLY your local PC's IP address
   - Never share your API keys or expose them in public repositories
   - Recommended permissions:
     - Read (Required)
     - Trade (Required for order execution)
     - Wallet (Required for balance checking)

## Environment Variables

The following environment variables need to be set:

```
MEMBER_ID=your_member_id
ACCESS_KEY=your_api_key
SECRET_KEY=your_api_secret
TESTNET=true_or_false
```

## Technical Indicators Configuration

Example strategy variables for backtesting:

```python
{
    'indicators': {
        'rsi': {'period': 14, 'buy_threshold': 30, 'sell_threshold': 70},
        'mfi': {'period': 14, 'buy_threshold': 20, 'sell_threshold': 80},
        'bollinger': {'period': 20, 'std_dev': 2.0},
        'sma': {'periods': [20, 50, 200]},
        'ema': {'periods': [9, 21, 55]}
    },
    'position': {
        'size': 100,  # % of balance
        'profit_target': 0.5,  # %
        'stop_loss': -0.3,  # %
        'trailing_stop': 0.2  # %
    },
    'filters': {
        'volume_threshold': 1000,
        'price_threshold': 50000
    }
}
```

## Important Notes

1. For spot trading:
   - Minimum order quantity: 0.000011 BTC (up to 6 decimal places)
   - Minimum order amount: 5 USDT
   - Market buy orders: quantity in USDT
   - Market sell orders: quantity in BTC
   - Limit orders: quantity in BTC

2. For futures trading:
   - Position index required:
     - Long position: 1
     - Short position: 2

## Security Warning

⚠️ NEVER commit your API keys to version control
⚠️ ALWAYS use IP restrictions for your API keys
⚠️ Monitor your API key usage regularly
⚠️ Revoke any compromised API keys immediately

🧠 MCP Server for Local Bybit API Access
This project provides a lightweight MCP (Model Context Protocol) server that allows local AI agents to interact with the Bybit API safely and efficiently. The server is designed to expose a conversational API interface while preserving execution context, enabling AI models (such as ChatGPT or other MCP-compatible clients) to interact with live market data, user account info, and order placement locally—without exposing API keys to the cloud.

✨ Key Features
🔒 Secure local access to the Bybit API (no cloud key exposure)

🤖 MCP-compatible server for context-aware agent interaction

⚡ Fast setup and extensible design

🛠️ Built with developers and quant researchers in mind

🧪 Use Cases
Real-time trading bot interaction with LLMs

Strategy debugging and backtesting conversations

Safe local experimentation with private Bybit credentials

## Contact & Support

For additional inquiries or support, please contact:
- Email: dlwjdtn5624@naver.com

We welcome your questions and feedback!

## Sponsorship & Donations

If you find this project helpful and would like to support its development, you can contribute in the following ways:


### Buy Me a Coffee
[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoffee.com/dlwjdtn535)

### Referral Program
You can also support this project by signing up for Bybit using our referral link:
- [My Bybit Referral Link](https://www.bybit.com/invite?ref=J1O4JK)
- Referral Code: J1O4JK

Your support helps maintain and improve this project. Thank you! 🙏

🧠 MCP Server for Local Bybit API Access
This project provides a lightweight MCP (Model Context Protocol) server that allows local AI agents to interact with the Bybit API safely and efficiently. The server is designed to expose a conversational API interface while preserving execution context, enabling AI models (such as ChatGPT or other MCP-compatible clients) to interact with live market data, user account info, and order placement locally—without exposing API keys to the cloud.

✨ Key Features
🔒 Secure local access to the Bybit API (no cloud key exposure)

🤖 MCP-compatible server for context-aware agent interaction

⚡ Fast setup and extensible design

🛠️ Built with developers and quant researchers in mind

🧪 Use Cases
Real-time trading bot interaction with LLMs

Strategy debugging and backtesting conversations

Safe local experimentation with private Bybit credentials

### Installing via Smithery

To install Bybit Trader for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@dlwjdtn535/mcp-bybit-trader):

```bash
npx -y @smithery/cli install @dlwjdtn535/mcp-bybit-trader --client claude
```

