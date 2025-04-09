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
mcp = FastMCP(
    title="MCP Bybit Trader",
    description="MCP-based Bybit Trading Bot",
    version="0.1.0",
    debug=True,  # Enable debug mode
    env={
        "MEMBER_ID": os.getenv("MEMBER_ID"),
        "ACCESS_KEY": os.getenv("ACCESS_KEY"),
        "SECRET_KEY": os.getenv("SECRET_KEY"),
        "TESTNET": os.getenv("TESTNET")
    }
)


# Register MCP tools
@mcp.tool()
def get_orderbook(
        category: str = Field(description="Category (spot, linear, inverse, etc.)"),
        symbol: str = Field(description="Symbol (e.g., BTCUSDT)"),
        limit: int = Field(default=50, description="Number of orderbook entries to retrieve")
) -> Dict:
    """
    Get orderbook data
    :parameter
        symbol: Symbol (e.g., BTCUSDT)
        limit: Number of orderbook entries to retrieve
        category: Category (spot, linear, inverse, etc.)

    Args:
        category: Category (spot, linear, inverse, etc.)
        symbol (str): Symbol (e.g., BTCUSDT)
        limit (int): Number of orderbook entries to retrieve

    Returns:
        Dict: Orderbook data

    Example:
        get_orderbook("spot", "BTCUSDT", 10)

    Reference:
        https://bybit-exchange.github.io/docs/v5/market/orderbook
    """
    try:
        result = bybit_service.get_orderbook(category, symbol, limit)
        if result.get("retCode") != 0:
            logger.error(f"Failed to get orderbook: {result.get('retMsg')}")
            return {"error": result.get("retMsg")}
        return result
    except Exception as e:
        logger.error(f"Failed to get orderbook: {e}", exc_info=True)
        return {"error": str(e)}


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


@mcp.tool()
def get_tickers(
        category: str = Field(description="Category (spot, linear, inverse, etc.)"),
        symbol: str = Field(description="Symbol (e.g., BTCUSDT)")
) -> Dict:
    """
    Get ticker information

    Args:
        category (str): Category (spot, linear, inverse, etc.)
        symbol (str): Symbol (e.g., BTCUSDT)

    Returns:
        Dict: Ticker information

    Example:
        get_tickers("spot", "BTCUSDT")

    Reference:
        https://bybit-exchange.github.io/docs/v5/market/tickers
    """
    try:
        result = bybit_service.get_tickers(category, symbol)
        if result.get("retCode") != 0:
            logger.error(f"Failed to get ticker information: {result.get('retMsg')}")
            return {"error": result.get("retMsg")}
        return result
    except Exception as e:
        logger.error(f"Failed to get ticker information: {e}", exc_info=True)
        return {"error": str(e)}


@mcp.tool()
def get_wallet_balance(
        accountType: str = Field(description="Account type (UNIFIED, CONTRACT, SPOT)"),
        coin: Optional[str] = Field(default=None, description="Coin symbol")
) -> Dict:
    """
    Get wallet balance

    Args:
        accountType (str): Account type (UNIFIED, CONTRACT, SPOT)
        coin (Optional[str]): Coin symbol

    Returns:
        Dict: Wallet balance information

    Example:
        get_wallet_balance("UNIFIED", "BTC")

    Reference:
        https://bybit-exchange.github.io/docs/v5/account/wallet-balance
    """
    try:
        result = bybit_service.get_wallet_balance(accountType, coin)
        if result.get("retCode") != 0:
            logger.error(f"Failed to get wallet balance: {result.get('retMsg')}")
            return {"error": result.get("retMsg")}
        return result
    except Exception as e:
        logger.error(f"Failed to get wallet balance: {e}", exc_info=True)
        return {"error": str(e)}


@mcp.tool()
def get_positions(
        category: str = Field(description="Category (spot, linear, inverse, etc.)"),
        symbol: Optional[str] = Field(default=None, description="Symbol (e.g., BTCUSDT)")
) -> Dict:
    """
    Get position information

    Args:
        category (str): Category (spot, linear, inverse, etc.)
        symbol (Optional[str]): Symbol (e.g., BTCUSDT)

    Returns:
        Dict: Position information

    Example:
        get_positions("spot", "BTCUSDT")

    Reference:
        https://bybit-exchange.github.io/docs/v5/position
    """
    try:
        result = bybit_service.get_positions(category, symbol)
        if result.get("retCode") != 0:
            logger.error(f"Failed to get position information: {result.get('retMsg')}")
            return {"error": result.get("retMsg")}
        return result
    except Exception as e:
        logger.error(f"Failed to get position information: {e}", exc_info=True)
        return {"error": str(e)}


@mcp.tool()
def place_order(
        category: str = Field(description="Category (spot, linear, inverse, etc.)"),
        symbol: str = Field(description="Symbol (e.g., BTCUSDT)"),
        side: str = Field(description="Order direction (Buy, Sell)"),
        orderType: str = Field(description="Order type (Market, Limit)"),
        qty: str = Field(description="Order quantity"),
        price: Optional[str] = Field(default=None, description="Order price (for limit orders)"),
        positionIdx: Optional[str] = Field(default=None, description="Position index (1: Long, 2: Short)"),
        timeInForce: Optional[str] = Field(default=None, description="Time in force (GTC, IOC, FOK, PostOnly)"),
        orderLinkId: Optional[str] = Field(default=None, description="Order link ID"),
        isLeverage: Optional[int] = Field(default=None, description="Use leverage (0: No, 1: Yes)"),
        orderFilter: Optional[str] = Field(default=None, description="Order filter (Order, tpslOrder, StopOrder)"),
        triggerPrice: Optional[str] = Field(default=None, description="Trigger price"),
        triggerBy: Optional[str] = Field(default=None, description="Trigger basis"),
        orderIv: Optional[str] = Field(default=None, description="Order volatility"),
        takeProfit: Optional[str] = Field(default=None, description="Take profit price"),
        stopLoss: Optional[str] = Field(default=None, description="Stop loss price"),
        tpTriggerBy: Optional[str] = Field(default=None, description="Take profit trigger basis"),
        slTriggerBy: Optional[str] = Field(default=None, description="Stop loss trigger basis"),
        tpLimitPrice: Optional[str] = Field(default=None, description="Take profit limit price"),
        slLimitPrice: Optional[str] = Field(default=None, description="Stop loss limit price"),
        tpOrderType: Optional[str] = Field(default=None, description="Take profit order type (Market, Limit)"),
        slOrderType: Optional[str] = Field(default=None, description="Stop loss order type (Market, Limit)")
) -> Dict:
    """
    Execute order

    Args:
        category (str): Category
            - spot: Spot trading
                * Minimum order quantity: 0.000011 BTC (up to 6 decimal places)
                * Minimum order amount: 5 USDT
                * If buying at market price, qty should be input in USDT units (e.g., "10" = 10 USDT)
                * If selling at market price, qty should be input in BTC units (e.g., "0.000100" = 0.0001 BTC)
                * If placing a limit order, qty should be input in BTC units
                * positionIdx is not used
            - linear: Futures trading (USDT margin)
                * positionIdx is required (1: Long, 2: Short)
            - inverse: Futures trading (coin margin)
                * positionIdx is required (1: Long, 2: Short)
        symbol (str): Symbol (e.g., BTCUSDT)
        side (str): Order direction (Buy, Sell)
        orderType (str): Order type (Market, Limit)
        qty (str): Order quantity
            - Market Buy: qty should be input in USDT units (e.g., "10" = 10 USDT)
            - Market Sell: qty should be input in BTC units (e.g., "0.000100" = 0.0001 BTC, up to 6 decimal places)
            - Limit: qty should be input in BTC units (e.g., "0.000100" = 0.0001 BTC, up to 6 decimal places)
        price (Optional[str]): Order price (for limit orders)
        positionIdx (Optional[str]): Position index
            - Required for futures (linear/inverse) trading
            - "1": Long position
            - "2": Short position
            - Not used for spot trading
        timeInForce (Optional[str]): Order validity period
            - GTC: Good Till Cancel (default, for limit orders)
            - IOC: Immediate or Cancel (market order)
            - FOK: Fill or Kill
            - PostOnly: Post Only
        orderLinkId (Optional[str]): Order link ID (unique value)
        isLeverage (Optional[int]): Use leverage (0: No, 1: Yes)
        orderFilter (Optional[str]): Order filter
            - Order: Regular order (default)
            - tpslOrder: TP/SL order
            - StopOrder: Stop order
        triggerPrice (Optional[str]): Trigger price
        triggerBy (Optional[str]): Trigger basis
        orderIv (Optional[str]): Order volatility
        takeProfit (Optional[str]): Take profit price
        stopLoss (Optional[str]): Stop loss price
        tpTriggerBy (Optional[str]): Take profit trigger basis
        slTriggerBy (Optional[str]): Stop loss trigger basis
        tpLimitPrice (Optional[str]): Take profit limit price
        slLimitPrice (Optional[str]): Stop loss limit price
        tpOrderType (Optional[str]): Take profit order type (Market, Limit)
        slOrderType (Optional[str]): Stop loss order type (Market, Limit)

    Returns:
        Dict: Order result

    Example:
        # Spot trading (SPOT account balance required)
        place_order("spot", "BTCUSDT", "Buy", "Market", "10")  # Buy market price for 10 USDT
        place_order("spot", "BTCUSDT", "Sell", "Market", "0.000100")  # Sell market price for 0.0001 BTC
        place_order("spot", "BTCUSDT", "Buy", "Limit", "0.000100", price="50000")  # Buy limit order for 0.0001 BTC

        # Spot trading - limit order + TP/SL
        place_order("spot", "BTCUSDT", "Buy", "Limit", "0.000100", price="50000",
                   takeProfit="55000", stopLoss="45000",  # TP/SL setting
                   tpOrderType="Market", slOrderType="Market")  # Execute TP/SL as market order

        # Futures trading
        place_order("linear", "BTCUSDT", "Buy", "Market", "0.001", positionIdx="1")  # Buy market price for long position
        place_order("linear", "BTCUSDT", "Sell", "Market", "0.001", positionIdx="2")  # Sell market price for short position

    Notes:
        1. Spot trading order quantity restrictions:
            - Minimum order quantity: 0.000011 BTC
            - Minimum order amount: 5 USDT
            - BTC quantity is only allowed up to 6 decimal places (e.g., 0.000100 O, 0.0001234 X)
        2. Pay attention to unit when buying/selling at market price:
            - Buying: qty should be input in USDT units (e.g., "10" = 10 USDT)
            - Selling: qty should be input in BTC units (e.g., "0.000100" = 0.0001 BTC)
        3. Futures trading requires positionIdx:
            - Long position: positionIdx="1"
            - Short position: positionIdx="2"
        4. positionIdx is not used for spot trading

    Reference:
        https://bybit-exchange.github.io/docs/v5/order/create-order
    """
    try:
        result = bybit_service.place_order(
            category, symbol, side, orderType, qty, price, positionIdx,
            timeInForce, orderLinkId, isLeverage, orderFilter,
            triggerPrice, triggerBy, orderIv, takeProfit,
            stopLoss, tpTriggerBy, slTriggerBy, tpLimitPrice,
            slLimitPrice, tpOrderType, slOrderType
        )
        if result.get("retCode") != 0:
            logger.error(f"Failed to place order: {result.get('retMsg')}")
            return {"error": result.get("retMsg")}
        return result
    except Exception as e:
        logger.error(f"Failed to place order: {e}", exc_info=True)
        return {"error": str(e)}


@mcp.tool()
def cancel_order(
        category: str = Field(description="Category (spot, linear, inverse, etc.)"),
        symbol: str = Field(description="Symbol (e.g., BTCUSDT)"),
        orderId: Optional[str] = Field(default=None, description="Order ID"),
        orderLinkId: Optional[str] = Field(default=None, description="Order link ID"),
        orderFilter: Optional[str] = Field(default=None, description="Order filter")
) -> Dict:
    """
    Cancel order

    Args:
        category (str): Category (spot, linear, inverse, etc.)
        symbol (str): Symbol (e.g., BTCUSDT)
        orderId (Optional[str]): Order ID
        orderLinkId (Optional[str]): Order link ID
        orderFilter (Optional[str]): Order filter

    Returns:
        Dict: Cancel result

    Example:
        cancel_order("spot", "BTCUSDT", "123456789")

    Reference:
        https://bybit-exchange.github.io/docs/v5/order/cancel-order
    """
    try:
        result = bybit_service.cancel_order(category, symbol, orderId, orderLinkId, orderFilter)
        if result.get("retCode") != 0:
            logger.error(f"Failed to cancel order: {result.get('retMsg')}")
            return {"error": result.get("retMsg")}
        return result
    except Exception as e:
        logger.error(f"Failed to cancel order: {e}", exc_info=True)
        return {"error": str(e)}


@mcp.tool()
def get_order_history(
        category: str = Field(description="Category (spot, linear, inverse, etc.)"),
        symbol: Optional[str] = Field(default=None, description="Symbol (e.g., BTCUSDT)"),
        orderId: Optional[str] = Field(default=None, description="Order ID"),
        orderLinkId: Optional[str] = Field(default=None, description="Order link ID"),
        orderFilter: Optional[str] = Field(default=None, description="Order filter"),
        orderStatus: Optional[str] = Field(default=None, description="Order status"),
        startTime: Optional[int] = Field(default=None, description="Start time in milliseconds"),
        endTime: Optional[int] = Field(default=None, description="End time in milliseconds"),
        limit: int = Field(default=50, description="Number of orders to retrieve")
) -> Dict:
    """
    Get order history

    Args:
        category (str): Category (spot, linear, inverse, etc.)
        symbol (Optional[str]): Symbol (e.g., BTCUSDT)
        orderId (Optional[str]): Order ID
        orderLinkId (Optional[str]): Order link ID
        orderFilter (Optional[str]): Order filter
        orderStatus (Optional[str]): Order status
        startTime (Optional[int]): Start time in milliseconds
        endTime (Optional[int]): End time in milliseconds
        limit (int): Number of orders to retrieve

    Returns:
        Dict: Order history

    Example:
        get_order_history("spot", "BTCUSDT", "123456789", "link123", "Order", "Created", 1625097600000, 1625184000000, 10)

    Reference:
        https://bybit-exchange.github.io/docs/v5/order/order-list
    """
    try:
        result = bybit_service.get_order_history(
            category, symbol, orderId, orderLinkId,
            orderFilter, orderStatus, startTime, endTime, limit
        )
        if result.get("retCode") != 0:
            logger.error(f"Failed to get order history: {result.get('retMsg')}")
            return {"error": result.get("retMsg")}
        return result
    except Exception as e:
        logger.error(f"Failed to get order history: {e}", exc_info=True)
        return {"error": str(e)}


@mcp.tool()
def get_open_orders(
        category: str = Field(description="Category (spot, linear, inverse, etc.)"),
        symbol: Optional[str] = Field(default=None, description="Symbol (e.g., BTCUSDT)"),
        orderId: Optional[str] = Field(default=None, description="Order ID"),
        orderLinkId: Optional[str] = Field(default=None, description="Order link ID"),
        orderFilter: Optional[str] = Field(default=None, description="Order filter"),
        limit: int = Field(default=50, description="Number of orders to retrieve")
) -> Dict:
    """
    Get open orders

    Args:
        category (str): Category (spot, linear, inverse, etc.)
        symbol (Optional[str]): Symbol (e.g., BTCUSDT)
        orderId (Optional[str]): Order ID
        orderLinkId (Optional[str]): Order link ID
        orderFilter (Optional[str]): Order filter
        limit (int): Number of orders to retrieve

    Returns:
        Dict: Open orders

    Example:
        get_open_orders("spot", "BTCUSDT", "123456789", "link123", "Order", 10)

    Reference:
        https://bybit-exchange.github.io/docs/v5/order/open-order
    """
    try:
        result = bybit_service.get_open_orders(
            category, symbol, orderId, orderLinkId, orderFilter, limit
        )
        if result.get("retCode") != 0:
            logger.error(f"Failed to get open orders: {result.get('retMsg')}")
            return {"error": result.get("retMsg")}
        return result
    except Exception as e:
        logger.error(f"Failed to get open orders: {e}", exc_info=True)
        return {"error": str(e)}


@mcp.tool()
def set_trading_stop(
        category: str = Field(description="Category (spot, linear, inverse, etc.)"),
        symbol: str = Field(description="Symbol (e.g., BTCUSDT)"),
        takeProfit: Optional[str] = Field(default=None, description="Take profit price"),
        stopLoss: Optional[str] = Field(default=None, description="Stop loss price"),
        trailingStop: Optional[str] = Field(default=None, description="Trailing stop"),
        positionIdx: Optional[int] = Field(default=None, description="Position index")
) -> Dict:
    """
    Set trading stop

    Args:
        category (str): Category (spot, linear, inverse, etc.)
        symbol (str): Symbol (e.g., BTCUSDT)
        takeProfit (Optional[str]): Take profit price
        stopLoss (Optional[str]): Stop loss price
        trailingStop (Optional[str]): Trailing stop
        positionIdx (Optional[int]): Position index

    Returns:
        Dict: Setting result

    Example:
        set_trading_stop("spot", "BTCUSDT", "55000", "45000", "1000", 0)

    Reference:
        https://bybit-exchange.github.io/docs/v5/position/trading-stop
    """
    try:
        result = bybit_service.set_trading_stop(
            category, symbol, takeProfit, stopLoss, trailingStop, positionIdx
        )
        if result.get("retCode") != 0:
            logger.error(f"Failed to set trading stop: {result.get('retMsg')}")
            return {"error": result.get("retMsg")}
        return result
    except Exception as e:
        logger.error(f"Failed to set trading stop: {e}", exc_info=True)
        return {"error": str(e)}


@mcp.tool()
def set_margin_mode(
        category: str = Field(description="Category (spot, linear, inverse, etc.)"),
        symbol: str = Field(description="Symbol (e.g., BTCUSDT)"),
        tradeMode: int = Field(description="Trading mode (0: Isolated, 1: Cross)"),
        buyLeverage: str = Field(description="Buying leverage"),
        sellLeverage: str = Field(description="Selling leverage")
) -> Dict:
    """
    Set margin mode

    Args:
        category (str): Category (spot, linear, inverse, etc.)
        symbol (str): Symbol (e.g., BTCUSDT)
        tradeMode (int): Trading mode (0: Isolated, 1: Cross)
        buyLeverage (str): Buying leverage
        sellLeverage (str): Selling leverage

    Returns:
        Dict: Setting result

    Example:
        set_margin_mode("spot", "BTCUSDT", 0, "10", "10")

    Reference:
        https://bybit-exchange.github.io/docs/v5/account/set-margin-mode
    """
    try:
        result = bybit_service.set_margin_mode(
            category, symbol, tradeMode, buyLeverage, sellLeverage
        )
        if result.get("retCode") != 0:
            logger.error(f"Failed to set margin mode: {result.get('retMsg')}")
            return {"error": result.get("retMsg")}
        return result
    except Exception as e:
        logger.error(f"Failed to set margin mode: {e}", exc_info=True)
        return {"error": str(e)}


@mcp.tool()
def get_api_key_information() -> Dict:
    """
    Get API key information

    Returns:
        Dict: API key information

    Example:
        get_api_key_information()

    Reference:
        https://bybit-exchange.github.io/docs/v5/user/apikey-info
    """
    try:
        result = bybit_service.get_api_key_information()
        if result.get("retCode") != 0:
            logger.error(f"Failed to get API key information: {result.get('retMsg')}")
            return {"error": result.get("retMsg")}
        return result
    except Exception as e:
        logger.error(f"Failed to get API key information: {e}", exc_info=True)
        return {"error": str(e)}


@mcp.tool()
def get_instruments_info(
        category: str = Field(description="Category (spot, linear, inverse, etc.)"),
        symbol: str = Field(description="Symbol (e.g., BTCUSDT)"),
        status: Optional[str] = Field(default=None, description="Status"),
        baseCoin: Optional[str] = Field(default=None, description="Base coin")
) -> Dict:
    """
    Get exchange information

    Args:
        category (str): Category (spot, linear, inverse, etc.)
        symbol (str): Symbol (e.g., BTCUSDT)
        status (Optional[str]): Status
        baseCoin (Optional[str]): Base coin

    Returns:
        Dict: Exchange information

    Example:
        get_instruments_info("spot", "BTCUSDT", "Trading", "BTC")

    Reference:
        https://bybit-exchange.github.io/docs/v5/market/instrument
    """
    try:
        result = bybit_service.get_instruments_info(category, symbol, status, baseCoin)
        if result.get("retCode") != 0:
            logger.error(f"Failed to get instruments information: {result.get('retMsg')}")
            return {"error": result.get("retMsg")}
        return result
    except Exception as e:
        logger.error(f"Failed to get instruments information: {e}", exc_info=True)
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

        mcp.run(transport="sse")
    except Exception as e:
        logger.error(e)
        print(f"Server execution failed: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()