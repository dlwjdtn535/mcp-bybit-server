# MCP Bybit Trader
[![smithery badge](https://smithery.ai/badge/@dlwjdtn535/bybit-trader)](https://smithery.ai/server/@dlwjdtn535/bybit-trader)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-support-yellow.svg)](https://buymeacoffee.com/dlwjdtn535)

Bybit MCP (Model Context Protocol) Server. Allows interaction with the Bybit API to fetch cryptocurrency information, manage transactions, and perform backtesting.

## Usage

### Installing via Smithery

To install Bybit Trader for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@dlwjdtn535/bybit-trader):

```bash
npx -y @smithery/cli install @dlwjdtn535/bybit-trader --client claude
```

### Using with Claude, Roo Code, Cline, etc.

Add the following configuration to your MCP settings file (e.g., `mcp_settings.json`):

**Using Docker (Requires Docker)**

Make sure you have pulled the image first: `docker pull dlwjdtn535/mcp-bybit-trader:latest`

```json
{
  "mcpServers": {
    "bybit-trader-docker": {
      "command": "docker",
      "args": [
        "run",
        "--rm", // Automatically remove the container when it exits
        "-e", "ACCESS_KEY=${ACCESS_KEY}",
        "-e", "SECRET_KEY=${SECRET_KEY}",
        "-e", "TESTNET=${TESTNET}", // Ensure these env vars are set in your client's environment
        "dlwjdtn535/mcp-bybit-trader:latest"
      ],
      "env": { 
        // Environment variables for the docker command itself,
        // passed via -e args above. Ensure ACCESS_KEY, SECRET_KEY, TESTNET are available
        // in the environment where your MCP client (Claude, Roo Code, etc.) runs.
        "ACCESS_KEY": "YOUR_BYBIT_API_KEY", // Required - Set here or in client env
        "SECRET_KEY": "YOUR_BYBIT_SECRET_KEY", // Required - Set here or in client env
        "TESTNET": "false" // Optional - Set here or in client env
       },
      "disabled": false
    }
  }
}
```

> **Note**: Always use `@latest` or a specific version tag for both NPX and Docker to ensure you are using the intended version.

## Tools 🛠️

This MCP server provides the following tools for interacting with the Bybit API:

1.  **`get_orderbook`**: Fetches order book information.
    *   Inputs: `category`, `symbol`, `limit` (optional)
    *   Returns: Order book details.
2.  **`get_kline`**: Fetches K-line (candlestick) data.
    *   Inputs: `category`, `symbol`, `interval`, `start` (optional), `end` (optional), `limit` (optional)
    *   Returns: Candlestick data.
3.  **`get_talib_kline`**: Fetches K-line data with technical indicators calculated using TA-Lib.
    *   Inputs: `category`, `symbol`, `interval`, `start` (optional), `end` (optional), `limit` (optional), `indicators` (optional dictionary)
    *   Returns: Candlestick data with indicators.
4.  **`get_tickers`**: Fetches cryptocurrency ticker information.
    *   Inputs: `category`, `symbol`
    *   Returns: Ticker information.
5.  **`get_wallet_balance`**: Fetches account balance.
    *   Inputs: `accountType`, `coin` (optional)
    *   Returns: Balance information.
6.  **`get_positions`**: Fetches position information.
    *   Inputs: `category`, `symbol` (optional)
    *   Returns: Position information.
7.  **`place_order`**: Places a limit or market order.
    *   Inputs: `category`, `symbol`, `side`, `orderType`, `qty`, `price` (optional for limit), `positionIdx` (optional for futures), and other optional parameters (e.g., `timeInForce`, `takeProfit`, `stopLoss`).
    *   Returns: Order placement confirmation.
8.  **`cancel_order`**: Cancels an existing order.
    *   Inputs: `category`, `symbol`, `orderId` (optional), `orderLinkId` (optional)
    *   Returns: Cancellation confirmation.
9.  **`get_order_history`**: Fetches historical order details.
    *   Inputs: `category`, `symbol` (optional), `orderId` (optional), `limit` (optional), etc.
    *   Returns: Order history.
10. **`get_open_orders`**: Fetches current open orders.
    *   Inputs: `category`, `symbol` (optional), `limit` (optional), etc.
    *   Returns: Open order details.
11. **`set_trading_stop`**: Sets take profit, stop loss, or trailing stop for a position.
    *   Inputs: `category`, `symbol`, `takeProfit` (optional), `stopLoss` (optional), `trailingStop` (optional), `positionIdx` (optional)
    *   Returns: Setting confirmation.
12. **`set_margin_mode`**: Sets the margin mode (isolated or cross).
    *   Inputs: `category`, `symbol`, `tradeMode`, `buyLeverage`, `sellLeverage`
    *   Returns: Setting confirmation.
13. **`get_api_key_information`**: Fetches information about the current API key.
    *   Inputs: None
    *   Returns: API key details.
14. **`get_instruments_info`**: Fetches details about trading instruments (symbols).
    *   Inputs: `category`, `symbol`, `status` (optional), `baseCoin` (optional)
    *   Returns: Instrument details.

_(Refer to the function docstrings in the code for detailed parameter descriptions and examples.)_

## Environment Variables

Before running the server, you **must** set the following environment variables:

```bash
ACCESS_KEY=YOUR_BYBIT_API_KEY
SECRET_KEY=YOUR_BYBIT_SECRET_KEY
TESTNET=false # Optional: set to true for testnet
```

## API Key Setup

To use this trading bot, you need to create an API key from Bybit. Follow these important steps:

1.  Go to Bybit and log into your account.
2.  Navigate to API Management.
3.  Create a new API key.
4.  **Important Security Settings:**
    *   Enable IP restriction if possible.
    *   Add ONLY the IP address(es) from which the server will run (your local PC IP, server IP, or Docker container's external IP).
    *   Never share your API keys or expose them in public repositories.
    *   Recommended permissions:
        *   Read (Required)
        *   Trade (Required for order execution)
        *   Wallet (Required for balance checking)

## Security Warning

⚠️ NEVER commit your API keys to version control.
⚠️ ALWAYS use IP restrictions for your API keys if possible.
⚠️ Monitor your API key usage regularly.
⚠️ Revoke any compromised API keys immediately.

## Sponsorship & Donations

If you find this project helpful and would like to support its development, you can contribute in the following ways:

### Buy Me a Coffee
[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoffee.com/dlwjdtn535)

### Referral Program
You can also support this project by signing up for Bybit using our referral link:
- [My Bybit Referral Link](https://www.bybit.com/invite?ref=J1O4JK)
- Referral Code: J1O4JK

Your support helps maintain and improve this project. Thank you! 🙏

## Contact & Support

For additional inquiries or support, please contact:
- Email: dlwjdtn5624@naver.com

We welcome your questions and feedback!

## License

MIT License

