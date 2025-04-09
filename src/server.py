import logging
import os
import sys
from typing import Dict, Optional

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from service import BybitService

# Logging configuration
logging.basicConfig(
    level=logging.DEBUG,  # Change logging level to DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Log environment variables
logger.debug("Current environment variables:")
for key, value in os.environ.items():
    if key in ["MEMBER_ID", "ACCESS_KEY", "SECRET_KEY", "TESTNET"]:
        logger.debug(f"{key}: {value}")


# Create BybitService instance
bybit_service = BybitService()

# Register MCP tools
mcp = FastMCP()


@mcp.tool()
def get_kline(
        category: str = Field(description="Category (spot, linear, inverse, etc.)"),
        symbol: str = Field(description="Symbol (e.g., BTCUSDT)"),
        interval: str = Field(description="Time interval (1, 3, 5, 15, 30, 60, 120, 240, 360, 720, D, W, M)"),
        start: Optional[int] = Field(default=None, description="Start time in milliseconds"),
        end: Optional[int] = Field(default=None, description="End time in milliseconds"),
        limit: int = Field(default=200, description="Number of records to retrieve")
) -> Dict:
    """
    Get K-line (candlestick) data

    Args:
        category (str): Category (spot, linear, inverse, etc.)
        symbol (str): Symbol (e.g., BTCUSDT)
        interval (str): Time interval (1, 3, 5, 15, 30, 60, 120, 240, 360, 720, D, W, M)
        start (Optional[int]): Start time in milliseconds
        end (Optional[int]): End time in milliseconds
        limit (int): Number of records to retrieve

    Returns:
        Dict: K-line data

    Example:
        get_kline("spot", "BTCUSDT", "1h", 1625097600000, 1625184000000, 100)

    Reference:
        https://bybit-exchange.github.io/docs/v5/market/kline
    """
    try:
        result = bybit_service.get_kline(category, symbol, interval, start, end, limit)
        if result.get("retCode") != 0:
            logger.error(f"Failed to get K-line data: {result.get('retMsg')}")
            return {"error": result.get("retMsg")}
        return result
    except Exception as e:
        logger.error(f"Failed to get K-line data: {e}", exc_info=True)
        return {"error": str(e)}



@mcp.prompt()
def prompt(message: str) -> str:
    return f"""
You are an AI trader trading Bitcoin. Bybit API is used to analyze market data, execute orders, and manage positions.

Available tools:
- get_orderbook(category, symbol, limit) - Get orderbook: Retrieve orderbook information for a specific category and symbol. limit parameter can be used to specify the number of orderbook entries to retrieve.
- get_kline(category, symbol, interval, start, end, limit) - Get K-line data: Retrieve K-line data for a specific category and symbol. interval, start, end, and limit parameters can be used to specify the retrieval range and number of records.
- get_talib_kline(category, symbol, interval, start, end, limit, indicators) - Get K-line data with technical indicators: Retrieve K-line data and calculate technical indicators using talib. indicators parameter can be used to specify additional indicators and their parameters.
- get_tickers(category, symbol) - Get ticker information: Retrieve ticker information for a specific category and symbol.
- get_trades(category, symbol, limit) - Get recent trade history: Retrieve recent trade history for a specific category and symbol. limit parameter can be used to specify the number of trades to retrieve.
- get_wallet_balance(accountType, coin) - Get wallet balance: Retrieve wallet balance information for a specific account type and coin.
- get_positions(category, symbol) - Get position information: Retrieve position information for a specific category and symbol.
- place_order(category, symbol, side, orderType, qty, price, timeInForce, orderLinkId, isLeverage, orderFilter, triggerPrice, triggerBy, orderIv, positionIdx) - Execute order: Execute an order. Various parameters can be used to specify the details of the order.
- cancel_order(category, symbol, orderId, orderLinkId, orderFilter) - Cancel order: Cancel a specific order. orderId, orderLinkId, and orderFilter parameters can be used to specify the order to cancel.
- get_order_history(category, symbol, orderId, orderLinkId, orderFilter, orderStatus, startTime, endTime, limit) - Get order history: Retrieve order history. Various parameters can be used to specify the retrieval range and conditions.
- get_open_orders(category, symbol, orderId, orderLinkId, orderFilter, limit) - Get open orders: Retrieve open orders. limit parameter can be used to specify the number of orders to retrieve.
- get_leverage_info(category, symbol) - Get leverage information: Retrieve leverage information for a specific category and symbol.
- set_trading_stop(category, symbol, takeProfit, stopLoss, trailingStop, positionIdx) - Set trading stop: Set trading stop. takeProfit, stopLoss, trailingStop, and positionIdx parameters can be used to specify the settings.
- set_margin_mode(category, symbol, tradeMode, buyLeverage, sellLeverage) - Set margin mode: Set margin mode. tradeMode, buyLeverage, and sellLeverage parameters can be used to specify the settings.
- get_api_key_information() - Get API key information: Retrieve API key information.
- get_instruments_info(category, symbol, status, baseCoin) - Get exchange information: Retrieve exchange information. status and baseCoin parameters can be used to specify the retrieval conditions.
- initialize_backtest(start_time, end_time, initial_balance, strategy_vars) - Initialize backtest: Set up backtest configuration with initial balance and strategy variables. Strategy variables can include various technical indicators (RSI, MFI, Bollinger Bands, SMA, EMA), position settings (size, profit target, stop loss, trailing stop), and filters (volume threshold, price threshold).
- run_backtest(start_time, end_time, strategy_vars) - Run backtest: Execute backtest with specified strategy variables. The backtest will simulate trading based on historical data and the defined strategy rules. Returns detailed results including trade history, performance metrics, and final balance.

Example strategy variables for backtesting:
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

User message: {message}
"""


def main():
    try:
        logger.info("MCP server starting...")
        print("MCP server starting...", file=sys.stderr)

        # Log environment variables again
        logger.debug("Server start environment variables:")
        for key, value in os.environ.items():
            if key in ["MEMBER_ID", "ACCESS_KEY", "SECRET_KEY", "TESTNET"]:
                logger.debug(f"{key}: {value}")

        mcp.run(transport="stdio")
    except Exception as e:
        logger.error(e)
        print(f"Server execution failed: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()