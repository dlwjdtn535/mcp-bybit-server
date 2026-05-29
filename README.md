# MCP Bybit API Interface
[![smithery badge](https://smithery.ai/badge/@dlwjdtn535/mcp-bybit-server)](https://smithery.ai/server/@dlwjdtn535/mcp-bybit-server)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-support-yellow.svg)](https://buymeacoffee.com/dlwjdtn535)

Bybit MCP (Model Context Protocol) Server. Provides a convenient interface to interact with the [Bybit V5 API](https://bybit-exchange.github.io/docs/v5/intro) using MCP tools. Allows fetching market data, managing account information, and placing/canceling orders via API calls wrapped as tools.

<a href="https://glama.ai/mcp/servers/@dlwjdtn535/mcp-bybit-server">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@dlwjdtn535/mcp-bybit-server/badge" alt="Bybit Server MCP server" />
</a>

## ⚠️ Security & Safety

This server can place **real trades with real money**. Read this before configuring it:

- **Trading is disabled by default.** Mutating tools (`place_order`, `cancel_order`, `amend_order`, `cancel_all_orders`, `set_trading_stop`, `set_margin_mode`, `set_leverage`) return an error unless you explicitly set `TRADING_ENABLED=true`.
- **Use the testnet first.** Set `TESTNET=true` while you experiment. Combine with `TRADING_ENABLED=false` for a fully read-only setup, or set `READONLY_MODE=true` to hard-block every mutating tool regardless of other settings.
- **Order size is capped.** `MAX_ORDER_SIZE_USDT` (default `100`) limits the estimated notional value of an order to guard against accidental large trades.
- **API keys are never logged or exposed.** No tool returns your keys; logs only report whether a key is present.
- **Never commit your API keys.** Provide them through environment variables only.

## Installation

Requires Python 3.12+. This project uses [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/dlwjdtn535/mcp-bybit-server.git
cd mcp-bybit-server
uv sync
uv run mcp-bybit-server   # runs the MCP server over stdio
```

After install, the `mcp-bybit-server` command is the entry point used by the MCP client configs below.

### Installing via Smithery

To install this Bybit API Interface server for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@dlwjdtn535/mcp-bybit-server):

```bash
npx -y @smithery/cli install @dlwjdtn535/mcp-bybit-server --client claude
```

## Configuration (Claude Desktop, Cline, Roo Code, etc.)

Add one of the following to your MCP settings file (e.g. `claude_desktop_config.json` / `mcp_settings.json`).

**Using uv (run from a cloned repo):**

```json
{
  "mcpServers": {
    "bybit": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/mcp-bybit-server",
        "mcp-bybit-server"
      ],
      "env": {
        "ACCESS_KEY": "YOUR_BYBIT_API_KEY",
        "SECRET_KEY": "YOUR_BYBIT_SECRET_KEY",
        "TESTNET": "true",
        "TRADING_ENABLED": "false"
      }
    }
  }
}
```

On Windows, use an absolute path with double backslashes (e.g. `C:\\Users\\YOUR_USERNAME\\mcp-bybit-server`).

**Using Docker:**

First pull the image: `docker pull dlwjdtn535/mcp-bybit-server:latest`

```json
{
  "mcpServers": {
    "bybit-server-docker": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--init",
        "-e", "ACCESS_KEY=YOUR_BYBIT_API_KEY",
        "-e", "SECRET_KEY=YOUR_BYBIT_SECRET_KEY",
        "-e", "TESTNET=true",
        "-e", "TRADING_ENABLED=false",
        "-e", "MAX_ORDER_SIZE_USDT=100",
        "dlwjdtn535/mcp-bybit-server:latest"
      ]
    }
  }
}
```

> **Note**: Always use `@latest` or a specific version tag for both NPX and Docker to ensure you are using the intended version.

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ACCESS_KEY` | Yes | – | Bybit API key. |
| `SECRET_KEY` | Yes | – | Bybit API secret. |
| `MEMBER_ID` | No | – | Bybit member ID (optional). |
| `TESTNET` | No | `false` | Use the Bybit testnet when `true`. |
| `TRADING_ENABLED` | No | `false` | Must be `true` to allow any mutating/trading tool. |
| `READONLY_MODE` | No | `false` | When `true`, blocks every mutating tool (takes precedence over `TRADING_ENABLED`). |
| `MAX_ORDER_SIZE_USDT` | No | `100` | Caps the estimated notional value (USDT) of a single order. |
| `RESPONSE_VERBOSITY` | No | `normal` | `minimal` trims `get_tickers`/`get_positions` responses to core fields to save tokens; `normal`/`full` return the full payload. |

## Tools 🛠️

### Market data
- **`get_orderbook`** — order book (`category`, `symbol`, `limit?`).
- **`get_kline`** — candlesticks (`category`, `symbol`, `interval`, `start?`, `end?`, `limit?`).
- **`get_tickers`** — ticker info (`category`, `symbol`).
- **`get_public_trade_history`** — recent public trades (`category`, `symbol`, `limit?`).
- **`get_instruments_info`** — instrument metadata / limits (`category`, `symbol`, `status?`, `baseCoin?`).
- **`get_funding_rate_history`** — funding rate history for perps (`category`, `symbol`, `startTime?`, `endTime?`, `limit?`).
- **`get_open_interest`** — open interest over time (`category`, `symbol`, `intervalTime?`, ...).
- **`get_fee_rate`** — maker/taker fee rates (`category`, `symbol?`, `baseCoin?`).
- **`get_server_time`** — Bybit server time.
- **`market_snapshot`** — composite market view (orderbook + ticker + kline + instrument + recent trades, plus funding rate & open interest for futures) in a single call.

### Account
- **`get_wallet_balance`** — balances (`accountType`, `coin?`).
- **`get_positions`** — open positions (`category`, `symbol?`).
- **`get_order_history`** — historical orders.
- **`get_open_orders`** — current open orders.
- **`get_api_key_information`** — API key details.

### Trading (mutating — requires `TRADING_ENABLED=true`)
- **`validate_order`** — pre-flight validation; never places an order. Not blocked by trading flags.
- **`place_order`** — place an order; supports `dry_run=true` to validate without placing.
- **`amend_order`** — modify an existing order in place.
- **`cancel_order`** — cancel a single order.
- **`cancel_all_orders`** — cancel all open orders (optionally scoped).
- **`set_trading_stop`** — set take profit / stop loss / trailing stop.
- **`set_margin_mode`** — set isolated/cross margin.
- **`set_leverage`** — set leverage for a futures symbol.

_(Refer to the function docstrings in the code for detailed parameter descriptions and examples.)_

## API Key Setup

To use this Bybit API interface, create an API key from Bybit:

1.  Log into your Bybit account.
2.  Navigate to API Management.
3.  Create a new API key.
4.  **Important security settings:**
    *   Enable IP restriction if possible, and add ONLY the IP address(es) the server runs from.
    *   Never share your API keys or expose them in public repositories.
    *   Recommended permissions:
        *   Read (required)
        *   Trade (required only if you enable order execution)
        *   Wallet (required for balance checking)

## Development

```bash
uv sync --group dev   # install dev dependencies (pytest, ruff)
uv run ruff check .   # lint
uv run pytest -q      # run the unit test suite (no live API calls)
```

CI (GitHub Actions) runs lint + tests on every push/PR; Docker images are built and published automatically on pushes to `main`.

## Sponsorship & Donations

If you find this project helpful and would like to support its development:

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

[MIT License](LICENSE)
