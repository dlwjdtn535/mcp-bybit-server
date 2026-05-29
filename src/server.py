import logging
import sys
from typing import Dict, Optional

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from config import MAX_ORDER_SIZE_USDT, Config
from service import BybitService

# Logging configuration
logging.basicConfig(
    level=logging.INFO,  # Change logging level to DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# SECURITY: API keys are never logged and never exposed through any tool.

# Create BybitService instance
bybit_service = BybitService()

mcp = FastMCP(name="bybit")


def _trading_guard() -> Optional[Dict]:
    """Return an error dict if mutating actions are currently blocked, else None.

    READONLY_MODE takes precedence over TRADING_ENABLED. Every mutating tool must
    call this before touching the account.
    """
    if Config.READONLY_MODE:
        return {"error": "Read-only mode is enabled. Set READONLY_MODE=false to allow trading actions."}
    if not Config.TRADING_ENABLED:
        return {"error": "Trading is DISABLED. Set TRADING_ENABLED=true to enable."}
    return None


def _last_price(category: str, symbol: str) -> Optional[float]:
    """Best-effort last/mark price lookup used to estimate order notional. None on failure."""
    try:
        res = bybit_service.get_tickers(category, symbol)
        rows = (res or {}).get("result", {}).get("list") or []
        if rows:
            price = rows[0].get("lastPrice") or rows[0].get("markPrice")
            return float(price) if price is not None else None
    except Exception as e:  # noqa: BLE001 - estimation is best-effort
        logger.warning(f"Could not fetch reference price for {symbol}: {e}")
    return None


def _check_order_size(category: str, symbol: str, side: str,
                      orderType: str, qty: str, price: Optional[str]) -> Optional[Dict]:
    """Enforce MAX_ORDER_SIZE_USDT across spot and futures. Returns error dict or None.

    Estimates notional value in USDT: spot market buy uses qty directly (already USDT);
    spot limit and futures use qty * price (or qty * last price when no limit price).
    If the notional cannot be estimated, the order is allowed but a warning is logged.
    """
    try:
        qty_f = float(qty)
    except (TypeError, ValueError):
        return {"error": f"Invalid qty: {qty}. Must be a number."}

    notional: Optional[float] = None
    if category == "spot":
        if side == "Buy" and orderType == "Market":
            notional = qty_f  # qty is already in USDT for spot market buys
        elif price is not None:
            try:
                notional = qty_f * float(price)
            except (TypeError, ValueError):
                notional = None
    else:  # linear / inverse / option
        ref_price: Optional[float] = None
        if price is not None:
            try:
                ref_price = float(price)
            except (TypeError, ValueError):
                ref_price = None
        if ref_price is None:
            ref_price = _last_price(category, symbol)
        if ref_price is not None:
            notional = qty_f * ref_price

    if notional is None:
        logger.warning(
            f"Could not estimate notional for {symbol} ({category} {side} {orderType}); "
            f"MAX_ORDER_SIZE_USDT cap not enforced for this order."
        )
        return None
    if notional > MAX_ORDER_SIZE_USDT:
        return {
            "error": (
                f"Estimated order notional {notional:.2f} USDT exceeds MAX_ORDER_SIZE_USDT "
                f"({MAX_ORDER_SIZE_USDT}). Adjust the MAX_ORDER_SIZE_USDT env var to allow larger orders."
            )
        }
    return None


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
    slOrderType: Optional[str] = Field(default=None, description="Stop loss order type (Market, Limit)"),
    dry_run: bool = Field(default=False, description="If true, validate the order and return the request without placing it")
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
        # SECURITY: trading must be explicitly enabled (and not read-only)
        guard = _trading_guard()
        if guard:
            return guard

        # SECURITY: input validation
        if side not in ("Buy", "Sell"):
            return {"error": f"Invalid side: {side}. Must be 'Buy' or 'Sell'."}
        if orderType not in ("Market", "Limit"):
            return {"error": f"Invalid orderType: {orderType}. Must be 'Market' or 'Limit'."}
        if category not in ("spot", "linear", "inverse", "option"):
            return {"error": f"Invalid category: {category}. Must be 'spot', 'linear', 'inverse', or 'option'."}

        # SECURITY: enforce max order size across spot and futures
        size_error = _check_order_size(category, symbol, side, orderType, qty, price)
        if size_error:
            return size_error

        # Dry-run: return the validated request without placing the order
        if dry_run:
            return {
                "dry_run": True,
                "valid": True,
                "message": "Validation passed. Order was NOT placed (dry_run=true).",
                "request": {
                    "category": category, "symbol": symbol, "side": side,
                    "orderType": orderType, "qty": qty, "price": price,
                    "positionIdx": positionIdx,
                },
            }

        result = bybit_service.place_order(
            category=category, symbol=symbol, side=side, orderType=orderType,
            qty=qty, price=price, positionIdx=positionIdx,
            timeInForce=timeInForce, orderLinkId=orderLinkId,
            isLeverage=isLeverage, orderFilter=orderFilter,
            triggerPrice=triggerPrice, triggerBy=triggerBy, orderIv=orderIv,
            takeProfit=takeProfit, stopLoss=stopLoss,
            tpTriggerBy=tpTriggerBy, slTriggerBy=slTriggerBy,
            tpLimitPrice=tpLimitPrice, slLimitPrice=slLimitPrice,
            tpOrderType=tpOrderType, slOrderType=slOrderType
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
        guard = _trading_guard()
        if guard:
            return guard
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
        guard = _trading_guard()
        if guard:
            return guard
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
        guard = _trading_guard()
        if guard:
            return guard
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


@mcp.tool()
def set_leverage(
    category: str = Field(description="Category (linear, inverse)"),
    symbol: str = Field(description="Symbol (e.g., BTCUSDT)"),
    buyLeverage: str = Field(description="Buy leverage (e.g., '10')"),
    sellLeverage: str = Field(description="Sell leverage (e.g., '10')")
) -> Dict:
    """
    Set leverage for a futures symbol.

    Args:
        category (str): Category (linear, inverse)
        symbol (str): Symbol (e.g., BTCUSDT)
        buyLeverage (str): Buy leverage
        sellLeverage (str): Sell leverage

    Returns:
        Dict: Setting result

    Example:
        set_leverage("linear", "BTCUSDT", "10", "10")

    Reference:
        https://bybit-exchange.github.io/docs/v5/position/leverage
    """
    try:
        guard = _trading_guard()
        if guard:
            return guard
        result = bybit_service.set_leverage(category, symbol, buyLeverage, sellLeverage)
        if result.get("retCode") != 0:
            logger.error(f"Failed to set leverage: {result.get('retMsg')}")
            return {"error": result.get("retMsg")}
        return result
    except Exception as e:
        logger.error(f"Failed to set leverage: {e}", exc_info=True)
        return {"error": str(e)}


@mcp.tool()
def get_public_trade_history(
    category: str = Field(description="Category (spot, linear, inverse, option)"),
    symbol: str = Field(description="Symbol (e.g., BTCUSDT)"),
    limit: int = Field(default=50, description="Number of recent trades to retrieve")
) -> Dict:
    """
    Get recent public trade (execution) history for a symbol.

    Args:
        category (str): Category (spot, linear, inverse, option)
        symbol (str): Symbol (e.g., BTCUSDT)
        limit (int): Number of trades to retrieve

    Returns:
        Dict: Recent public trades

    Example:
        get_public_trade_history("linear", "BTCUSDT", 50)

    Reference:
        https://bybit-exchange.github.io/docs/v5/market/recent-trade
    """
    try:
        result = bybit_service.get_public_trade_history(category, symbol, limit)
        if result.get("retCode") != 0:
            logger.error(f"Failed to get public trade history: {result.get('retMsg')}")
            return {"error": result.get("retMsg")}
        return result
    except Exception as e:
        logger.error(f"Failed to get public trade history: {e}", exc_info=True)
        return {"error": str(e)}


@mcp.tool()
def get_funding_rate_history(
    category: str = Field(description="Category (linear, inverse)"),
    symbol: str = Field(description="Symbol (e.g., BTCUSDT)"),
    startTime: Optional[int] = Field(default=None, description="Start time in milliseconds"),
    endTime: Optional[int] = Field(default=None, description="End time in milliseconds"),
    limit: int = Field(default=200, description="Number of records to retrieve")
) -> Dict:
    """
    Get historical funding rates for a perpetual/futures symbol.

    Args:
        category (str): Category (linear, inverse)
        symbol (str): Symbol (e.g., BTCUSDT)
        startTime (Optional[int]): Start time in milliseconds
        endTime (Optional[int]): End time in milliseconds
        limit (int): Number of records to retrieve

    Returns:
        Dict: Funding rate history

    Example:
        get_funding_rate_history("linear", "BTCUSDT", limit=10)

    Reference:
        https://bybit-exchange.github.io/docs/v5/market/history-fund-rate
    """
    try:
        result = bybit_service.get_funding_rate_history(category, symbol, startTime, endTime, limit)
        if result.get("retCode") != 0:
            logger.error(f"Failed to get funding rate history: {result.get('retMsg')}")
            return {"error": result.get("retMsg")}
        return result
    except Exception as e:
        logger.error(f"Failed to get funding rate history: {e}", exc_info=True)
        return {"error": str(e)}


@mcp.tool()
def get_open_interest(
    category: str = Field(description="Category (linear, inverse)"),
    symbol: str = Field(description="Symbol (e.g., BTCUSDT)"),
    intervalTime: str = Field(default="1h", description="Interval (5min, 15min, 30min, 1h, 4h, 1d)"),
    startTime: Optional[int] = Field(default=None, description="Start time in milliseconds"),
    endTime: Optional[int] = Field(default=None, description="End time in milliseconds"),
    limit: int = Field(default=50, description="Number of records to retrieve")
) -> Dict:
    """
    Get open interest of a symbol over time.

    Args:
        category (str): Category (linear, inverse)
        symbol (str): Symbol (e.g., BTCUSDT)
        intervalTime (str): Interval (5min, 15min, 30min, 1h, 4h, 1d)
        startTime (Optional[int]): Start time in milliseconds
        endTime (Optional[int]): End time in milliseconds
        limit (int): Number of records to retrieve

    Returns:
        Dict: Open interest data

    Example:
        get_open_interest("linear", "BTCUSDT", "1h", limit=24)

    Reference:
        https://bybit-exchange.github.io/docs/v5/market/open-interest
    """
    try:
        result = bybit_service.get_open_interest(category, symbol, intervalTime, startTime, endTime, limit)
        if result.get("retCode") != 0:
            logger.error(f"Failed to get open interest: {result.get('retMsg')}")
            return {"error": result.get("retMsg")}
        return result
    except Exception as e:
        logger.error(f"Failed to get open interest: {e}", exc_info=True)
        return {"error": str(e)}


@mcp.tool()
def get_fee_rate(
    category: str = Field(description="Category (spot, linear, inverse, option)"),
    symbol: Optional[str] = Field(default=None, description="Symbol (e.g., BTCUSDT)"),
    baseCoin: Optional[str] = Field(default=None, description="Base coin (e.g., BTC)")
) -> Dict:
    """
    Get maker/taker trading fee rates.

    Args:
        category (str): Category (spot, linear, inverse, option)
        symbol (Optional[str]): Symbol (e.g., BTCUSDT)
        baseCoin (Optional[str]): Base coin (e.g., BTC)

    Returns:
        Dict: Fee rate information

    Example:
        get_fee_rate("linear", "BTCUSDT")

    Reference:
        https://bybit-exchange.github.io/docs/v5/account/fee-rate
    """
    try:
        result = bybit_service.get_fee_rate(category, symbol, baseCoin)
        if result.get("retCode") != 0:
            logger.error(f"Failed to get fee rate: {result.get('retMsg')}")
            return {"error": result.get("retMsg")}
        return result
    except Exception as e:
        logger.error(f"Failed to get fee rate: {e}", exc_info=True)
        return {"error": str(e)}


@mcp.tool()
def get_server_time() -> Dict:
    """
    Get the Bybit server time (useful for clock synchronization).

    Returns:
        Dict: Server time

    Example:
        get_server_time()

    Reference:
        https://bybit-exchange.github.io/docs/v5/market/time
    """
    try:
        result = bybit_service.get_server_time()
        if result.get("retCode") != 0:
            logger.error(f"Failed to get server time: {result.get('retMsg')}")
            return {"error": result.get("retMsg")}
        return result
    except Exception as e:
        logger.error(f"Failed to get server time: {e}", exc_info=True)
        return {"error": str(e)}


@mcp.tool()
def amend_order(
    category: str = Field(description="Category (linear, inverse, spot, option)"),
    symbol: str = Field(description="Symbol (e.g., BTCUSDT)"),
    orderId: Optional[str] = Field(default=None, description="Order ID (either orderId or orderLinkId required)"),
    orderLinkId: Optional[str] = Field(default=None, description="Order link ID"),
    qty: Optional[str] = Field(default=None, description="New order quantity"),
    price: Optional[str] = Field(default=None, description="New order price"),
    triggerPrice: Optional[str] = Field(default=None, description="New trigger price"),
    takeProfit: Optional[str] = Field(default=None, description="New take profit price"),
    stopLoss: Optional[str] = Field(default=None, description="New stop loss price")
) -> Dict:
    """
    Amend (modify) an existing open order in place, instead of cancel + re-place.

    Args:
        category (str): Category (linear, inverse, spot, option)
        symbol (str): Symbol (e.g., BTCUSDT)
        orderId (Optional[str]): Order ID (either orderId or orderLinkId required)
        orderLinkId (Optional[str]): Order link ID
        qty (Optional[str]): New order quantity
        price (Optional[str]): New order price
        triggerPrice (Optional[str]): New trigger price
        takeProfit (Optional[str]): New take profit price
        stopLoss (Optional[str]): New stop loss price

    Returns:
        Dict: Amend result

    Example:
        amend_order("linear", "BTCUSDT", orderId="123", price="51000")

    Reference:
        https://bybit-exchange.github.io/docs/v5/order/amend-order
    """
    try:
        guard = _trading_guard()
        if guard:
            return guard
        if not orderId and not orderLinkId:
            return {"error": "Either orderId or orderLinkId is required."}
        result = bybit_service.amend_order(
            category, symbol, orderId, orderLinkId, qty, price, triggerPrice, takeProfit, stopLoss
        )
        if result.get("retCode") != 0:
            logger.error(f"Failed to amend order: {result.get('retMsg')}")
            return {"error": result.get("retMsg")}
        return result
    except Exception as e:
        logger.error(f"Failed to amend order: {e}", exc_info=True)
        return {"error": str(e)}


@mcp.tool()
def cancel_all_orders(
    category: str = Field(description="Category (spot, linear, inverse, option)"),
    symbol: Optional[str] = Field(default=None, description="Symbol (e.g., BTCUSDT)"),
    baseCoin: Optional[str] = Field(default=None, description="Base coin"),
    settleCoin: Optional[str] = Field(default=None, description="Settle coin (e.g., USDT)"),
    orderFilter: Optional[str] = Field(default=None, description="Order filter (Order, tpslOrder, StopOrder)")
) -> Dict:
    """
    Cancel all open orders, optionally scoped by symbol/baseCoin/settleCoin.

    Args:
        category (str): Category (spot, linear, inverse, option)
        symbol (Optional[str]): Symbol (e.g., BTCUSDT)
        baseCoin (Optional[str]): Base coin
        settleCoin (Optional[str]): Settle coin (e.g., USDT)
        orderFilter (Optional[str]): Order filter (Order, tpslOrder, StopOrder)

    Returns:
        Dict: Cancellation result (list of cancelled orders)

    Example:
        cancel_all_orders("linear", symbol="BTCUSDT")

    Reference:
        https://bybit-exchange.github.io/docs/v5/order/cancel-all
    """
    try:
        guard = _trading_guard()
        if guard:
            return guard
        result = bybit_service.cancel_all_orders(category, symbol, baseCoin, settleCoin, orderFilter)
        if result.get("retCode") != 0:
            logger.error(f"Failed to cancel all orders: {result.get('retMsg')}")
            return {"error": result.get("retMsg")}
        return result
    except Exception as e:
        logger.error(f"Failed to cancel all orders: {e}", exc_info=True)
        return {"error": str(e)}


@mcp.tool()
def market_snapshot(
    category: str = Field(description="Category (spot, linear, inverse)"),
    symbol: str = Field(description="Symbol (e.g., BTCUSDT)"),
    interval: str = Field(default="60", description="Kline interval (1, 5, 15, 60, 240, D, ...)"),
    kline_limit: int = Field(default=50, description="Number of kline records"),
    orderbook_limit: int = Field(default=25, description="Orderbook depth"),
    trades_limit: int = Field(default=25, description="Number of recent trades")
) -> Dict:
    """
    Composite market view in a single call: orderbook + ticker + kline + instrument info
    + recent trades (plus funding rate and open interest for linear/inverse). Reduces
    round-trips and token usage. Each section is independent: one failing call returns an
    {"error": ...} entry for that section without failing the whole snapshot.

    Args:
        category (str): Category (spot, linear, inverse)
        symbol (str): Symbol (e.g., BTCUSDT)
        interval (str): Kline interval
        kline_limit (int): Number of kline records
        orderbook_limit (int): Orderbook depth
        trades_limit (int): Number of recent trades

    Returns:
        Dict: Combined market snapshot

    Example:
        market_snapshot("linear", "BTCUSDT")
    """
    try:
        return bybit_service.market_snapshot(
            category, symbol, interval, kline_limit, orderbook_limit, trades_limit
        )
    except Exception as e:
        logger.error(f"Failed to build market snapshot: {e}", exc_info=True)
        return {"error": str(e)}


@mcp.tool()
def validate_order(
    category: str = Field(description="Category (spot, linear, inverse)"),
    symbol: str = Field(description="Symbol (e.g., BTCUSDT)"),
    side: str = Field(description="Order direction (Buy, Sell)"),
    orderType: str = Field(description="Order type (Market, Limit)"),
    qty: str = Field(description="Order quantity"),
    price: Optional[str] = Field(default=None, description="Order price (for limit orders)"),
    positionIdx: Optional[str] = Field(default=None, description="Position index (1: Long, 2: Short) for futures")
) -> Dict:
    """
    Pre-flight validation for an order WITHOUT placing it. Checks input fields, that the
    symbol exists and is trading, minimum order quantity from instrument info, and the
    MAX_ORDER_SIZE_USDT cap. Returns structured {valid, errors, warnings, info}.

    Use this before place_order to catch mistakes early. This is read-only and is NOT
    blocked by READONLY_MODE / TRADING_ENABLED.

    Args:
        category (str): Category (spot, linear, inverse)
        symbol (str): Symbol (e.g., BTCUSDT)
        side (str): Order direction (Buy, Sell)
        orderType (str): Order type (Market, Limit)
        qty (str): Order quantity
        price (Optional[str]): Order price (for limit orders)
        positionIdx (Optional[str]): Position index for futures (1: Long, 2: Short)

    Returns:
        Dict: {"valid": bool, "errors": [...], "warnings": [...], "info": {...}}

    Example:
        validate_order("spot", "BTCUSDT", "Buy", "Limit", "0.001", price="50000")
    """
    errors = []
    warnings = []
    info: Dict = {}
    try:
        if side not in ("Buy", "Sell"):
            errors.append(f"Invalid side: {side}. Must be 'Buy' or 'Sell'.")
        if orderType not in ("Market", "Limit"):
            errors.append(f"Invalid orderType: {orderType}. Must be 'Market' or 'Limit'.")
        if category not in ("spot", "linear", "inverse", "option"):
            errors.append(f"Invalid category: {category}.")
        if orderType == "Limit" and price is None:
            errors.append("price is required for Limit orders.")
        if category in ("linear", "inverse") and (positionIdx is None or str(positionIdx) not in ("1", "2")):
            errors.append("positionIdx ('1' Long / '2' Short) is required for futures.")

        try:
            qty_f = float(qty)
            if qty_f <= 0:
                errors.append("qty must be positive.")
        except (TypeError, ValueError):
            errors.append(f"Invalid qty: {qty}. Must be a number.")
            qty_f = None

        # Instrument check (symbol exists / trading status / min qty)
        instr = bybit_service.get_instruments_info(category, symbol)
        if instr.get("retCode") != 0:
            warnings.append(f"Could not fetch instrument info: {instr.get('retMsg')}")
        else:
            rows = instr.get("result", {}).get("list") or []
            if not rows:
                errors.append(f"Symbol {symbol} not found in category {category}.")
            else:
                row = rows[0]
                info["status"] = row.get("status")
                if row.get("status") and row.get("status") != "Trading":
                    warnings.append(f"Symbol status is '{row.get('status')}', not 'Trading'.")
                lot = row.get("lotSizeFilter") or {}
                min_qty = lot.get("minOrderQty") or lot.get("basePrecision")
                if min_qty is not None:
                    info["minOrderQty"] = min_qty
                    try:
                        if qty_f is not None and category != "spot" and qty_f < float(min_qty):
                            errors.append(f"qty {qty} is below minOrderQty {min_qty}.")
                    except (TypeError, ValueError):
                        pass

        # Size cap (reuses the same estimator as place_order)
        size_error = _check_order_size(category, symbol, side, orderType, qty, price)
        if size_error:
            errors.append(size_error["error"])

        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings, "info": info}
    except Exception as e:
        logger.error(f"Failed to validate order: {e}", exc_info=True)
        return {"valid": False, "errors": [str(e)], "warnings": warnings, "info": info}


@mcp.prompt()
def prompt(message: str) -> str:
    return f"""
You are an AI assistant providing access to the Bybit V5 API through the available tools.
Analyze user requests and use the appropriate tools to fetch market data, manage account
information, or execute/manage orders.

Safety: mutating tools (place_order, cancel_order, cancel_all_orders, amend_order,
set_trading_stop, set_margin_mode, set_leverage) are blocked unless TRADING_ENABLED=true,
and are always blocked when READONLY_MODE=true. Order size is capped by MAX_ORDER_SIZE_USDT.
Prefer validate_order (or place_order with dry_run=true) before placing real orders.

Market data tools:
- get_orderbook(category, symbol, limit)
- get_kline(category, symbol, interval, start, end, limit)
- get_tickers(category, symbol)
- get_public_trade_history(category, symbol, limit)
- get_instruments_info(category, symbol, status, baseCoin)
- get_funding_rate_history(category, symbol, startTime, endTime, limit)
- get_open_interest(category, symbol, intervalTime, startTime, endTime, limit)
- get_fee_rate(category, symbol, baseCoin)
- get_server_time()
- market_snapshot(category, symbol, interval, kline_limit, orderbook_limit, trades_limit) - composite market view in one call

Account tools:
- get_wallet_balance(accountType, coin)
- get_positions(category, symbol)
- get_order_history(category, symbol, orderId, orderLinkId, orderFilter, orderStatus, startTime, endTime, limit)
- get_open_orders(category, symbol, orderId, orderLinkId, orderFilter, limit)
- get_api_key_information()

Trading tools (mutating):
- validate_order(category, symbol, side, orderType, qty, price, positionIdx) - pre-flight check, never places an order
- place_order(category, symbol, side, orderType, qty, price, positionIdx, ..., dry_run)
- amend_order(category, symbol, orderId, orderLinkId, qty, price, triggerPrice, takeProfit, stopLoss)
- cancel_order(category, symbol, orderId, orderLinkId, orderFilter)
- cancel_all_orders(category, symbol, baseCoin, settleCoin, orderFilter)
- set_trading_stop(category, symbol, takeProfit, stopLoss, trailingStop, positionIdx)
- set_margin_mode(category, symbol, tradeMode, buyLeverage, sellLeverage)
- set_leverage(category, symbol, buyLeverage, sellLeverage)

User message: {message}
"""


def main():
    try:
        logger.info("MCP server starting...")
        print("MCP server starting...", file=sys.stderr)

        # SECURITY: API keys are never logged.

        mcp.run(transport="stdio")
    except Exception as e:
        logger.error(e)
        print(f"Server execution failed: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()