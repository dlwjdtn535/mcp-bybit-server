import logging
from typing import Dict, Optional
from pybit.unified_trading import HTTP
from config import Config
import pandas as pd
from talib import abstract

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


class BybitService:
    """
    Bybit API wrapper class
    """

    def __init__(self):
        """
        Initialize BybitService
        """
        logger.info(f"Initializing Bybit Service - Testnet: {Config.TESTNET}, API Key: {Config.ACCESS_KEY}")
        self.client = HTTP(
            testnet=Config.TESTNET,
            api_key=Config.ACCESS_KEY,
            api_secret=Config.SECRET_KEY
        )

    # Market data related methods
    def get_orderbook(self, category: str, symbol: str, limit: int = 50) -> Dict:
        """
        Get orderbook data

        Args:
            category (str): Category (spot, linear, inverse, etc.)
            symbol (str): Symbol (e.g., BTCUSDT)
            limit (int): Number of orderbook entries to retrieve

        Returns:
            Dict: Orderbook data
        """
        return self.client.get_orderbook(
            category=category,
            symbol=symbol,
            limit=limit
        )

    # @candle_cache.cache('category', 'symbol', 'interval', 'start', 'end', expire=3600)
    def get_kline(self, category: str, symbol: str, interval: str,
                  start: Optional[int] = None, end: Optional[int] = None,
                  limit: int = 200) -> Dict:
        """
        Get K-line data
        
        Args:
            category: Category (spot, linear, inverse, etc.)
            symbol: Symbol (e.g., BTCUSDT)
            interval: Time interval (1, 3, 5, 15, 30, 60, 120, 240, 360, 720, D, W, M)
            start: Start time (millisecond timestamp)
            end: End time (millisecond timestamp)
            limit: Number of records to retrieve
            
        Returns:
            Dict: K-line data
        """
        try:
            params = {
                "category": category,
                "symbol": symbol,
                "interval": interval,
                "limit": limit
            }
            
            if start:
                params["start"] = start
            if end:
                params["end"] = end
                
            response = self.client.get_kline(**params)
            return response
            
        except Exception as e:
            logger.error(f"Failed to get K-line data: {str(e)}")
            return {"error": str(e)}


    # @candle_cache.cache('category', 'symbol', 'interval', 'start', 'end', expire=3600)
    def get_talib_kline(self, category: str, symbol: str, interval: str,
                        start: Optional[int] = None, end: Optional[int] = None,
                        limit: int = 200, indicators: Optional[Dict] = None) -> Dict:
        """
        Get K-line data with TA-Lib indicators
        Args:
            category: Category (spot, linear, inverse, etc.)
            symbol: Symbol (e.g., BTCUSDT)
            interval: Time interval (1, 3, 5, 15, 30, 60, 120, 240, 360, 720, D, W, M)
            start: Start time (millisecond timestamp)
            end: End time (millisecond timestamp)
            limit: Number of records to retrieve
            indicators: Dictionary of indicators and their parameters.
                        Example: {
                            'SMA': [5, 10, 20],
                            'EMA': [10, 50],
                            'RSI': [{'timeperiod': 14}],
                            'MACD': [{'fastperiod': 12, 'slowperiod': 26, 'signalperiod': 9}]
                        }
        Returns:
            Dict: K-line data with TA-Lib indicators
        """
        try:
            # 1. Get K-line data first
            kline_response = self.get_kline(category, symbol, interval, start, end, limit)
            if kline_response.get("retCode") != 0 or "result" not in kline_response or "list" not in kline_response["result"]:
                logger.error(f"Failed to get base K-line data for TA-Lib calculation: {kline_response.get('retMsg')}")
                return kline_response # Return the original error response

            kline_data = kline_response["result"]["list"]
            if not kline_data:
                return kline_response # Return empty data if no kline data

            # 2. Convert to Pandas DataFrame
            # Adjust column names based on Bybit API v5 response structure
            # ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover']
            df = pd.DataFrame(kline_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'])
            # Convert timestamp to numeric first, then to datetime
            df['timestamp'] = pd.to_numeric(df['timestamp'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            # Convert other columns to numeric
            numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'turnover']
            df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric)

            # Reverse DataFrame as Bybit returns newest first, TA-Lib needs oldest first
            df = df.iloc[::-1]

            # 3. Calculate indicators if requested
            if indicators:
                indicator_results = {}
                for indicator_name, params_list in indicators.items():
                    # Use the imported abstract module directly
                    func = getattr(abstract, indicator_name.upper(), None)
                    if not func:
                        logger.warning(f"TA-Lib function {indicator_name.upper()} not found.")
                        continue

                    indicator_results[indicator_name] = {}
                    inputs = {
                        'open': df['open'],
                        'high': df['high'],
                        'low': df['low'],
                        'close': df['close'],
                        'volume': df['volume']
                    }

                    # If params_list is a list of integers (e.g., SMA: [5, 10])
                    if all(isinstance(p, int) for p in params_list):
                        for period in params_list:
                            try:
                                output = func(inputs, timeperiod=period)
                                # Handle multi-output indicators (like MACD, BBANDS)
                                if isinstance(output, pd.DataFrame):
                                     for col in output.columns:
                                         indicator_results[indicator_name][f'{col}_{period}'] = output[col].iloc[::-1].tolist() # Reverse back
                                else: # Single output indicator (like SMA, EMA)
                                     indicator_results[indicator_name][f'{indicator_name}_{period}'] = output.iloc[::-1].tolist() # Reverse back
                            except Exception as e:
                                logger.error(f"Error calculating {indicator_name} with period {period}: {e}")

                    # If params_list is a list of dictionaries (e.g., RSI: [{'timeperiod': 14}])
                    elif all(isinstance(p, dict) for p in params_list):
                         for params_dict in params_list:
                            param_key = '_'.join(f"{k}{v}" for k, v in params_dict.items()) # Create unique key like timeperiod14
                            try:
                                output = func(inputs, **params_dict)
                                if isinstance(output, pd.DataFrame):
                                     for col in output.columns:
                                         indicator_results[indicator_name][f'{col}_{param_key}'] = output[col].iloc[::-1].tolist() # Reverse back
                                else:
                                     indicator_results[indicator_name][f'{indicator_name}_{param_key}'] = output.iloc[::-1].tolist() # Reverse back
                            except Exception as e:
                                logger.error(f"Error calculating {indicator_name} with params {params_dict}: {e}")

            # 4. Prepare final result
            # Combine original kline data with calculated indicators
            final_result = kline_response # Start with original response
            final_result['result']['indicators'] = indicator_results if indicators else {}
            # Keep original kline list as is, indicators are separate
            # final_result['result']['list'] = df.iloc[::-1].reset_index().to_dict('records') # Convert back to list of dicts if needed

            return final_result

        except Exception as e:
            logger.error(f"Failed to get TA-Lib K-line data: {str(e)}", exc_info=True)
            return {"error": str(e)}

    def get_tickers(self, category: str, symbol: str) -> Dict:
        """
        Get ticker information

        Args:
            category (str): Category (spot, linear, inverse, etc.)
            symbol (str): Symbol (e.g., BTCUSDT)

        Returns:
            Dict: Ticker information
        """
        return self.client.get_tickers(
            category=category,
            symbol=symbol
        )

    # Account related methods
    def get_wallet_balance(self, accountType: str, coin: Optional[str] = None) -> Dict:
        """
        Get wallet balance

        Args:
            accountType (str): Account type (UNIFIED, CONTRACT, SPOT)
            coin (Optional[str]): Coin symbol

        Returns:
            Dict: Wallet balance information
        """
        return self.client.get_wallet_balance(
            accountType=accountType,
            coin=coin
        )

    def get_positions(self, category: str, symbol: Optional[str] = None) -> Dict:
        """
        Get position information

        Args:
            category (str): Category (spot, linear, inverse, etc.)
            symbol (Optional[str]): Symbol (e.g., BTCUSDT)

        Returns:
            Dict: Position information
        """
        return self.client.get_positions(
            category=category,
            symbol=symbol
        )

    # Order related methods
    def place_order(self, category: str, symbol: str, side: str, orderType: str,
                    qty: str, price: Optional[str] = None,
                    timeInForce: Optional[str] = None, orderLinkId: Optional[str] = None,
                    isLeverage: Optional[int] = None, orderFilter: Optional[str] = None,
                    triggerPrice: Optional[str] = None, triggerBy: Optional[str] = None,
                    orderIv: Optional[str] = None, positionIdx: Optional[int] = None,
                    takeProfit: Optional[str] = None, stopLoss: Optional[str] = None,
                    tpTriggerBy: Optional[str] = None, slTriggerBy: Optional[str] = None,
                    tpLimitPrice: Optional[str] = None, slLimitPrice: Optional[str] = None,
                    tpOrderType: Optional[str] = None, slOrderType: Optional[str] = None) -> Dict:
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
            price (Optional[str]): Order price (for limit order)
            timeInForce (Optional[str]): Order validity period
                - GTC: Good Till Cancel (default, for limit order)
                - IOC: Immediate or Cancel (market order)
                - FOK: Fill or Kill
                - PostOnly: Post Only
            orderLinkId (Optional[str]): Order link ID (unique value)
            isLeverage (Optional[int]): Use leverage (0: No use, 1: Use)
            orderFilter (Optional[str]): Order filter
                - Order: General order (default)
                - tpslOrder: TP/SL order
                - StopOrder: Stop order
            triggerPrice (Optional[str]): Trigger price
            triggerBy (Optional[str]): Trigger basis
            orderIv (Optional[str]): Order volatility
            positionIdx (Optional[int]): Position index
                - Required for futures (linear/inverse) trading
                - 1: Long position
                - 2: Short position
                - positionIdx is not used for spot trading
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
            place_order("linear", "BTCUSDT", "Buy", "Market", "0.001", positionIdx=1)  # Buy market price for long position
            place_order("linear", "BTCUSDT", "Sell", "Market", "0.001", positionIdx=2)  # Sell market price for short position

        Notes:
            1. Spot trading order quantity restrictions:
                - Minimum order quantity: 0.000011 BTC
                - Minimum order amount: 5 USDT
                - BTC quantity is only allowed up to 6 decimal places (e.g., 0.000100 O, 0.0001234 X)
            2. Pay attention to unit when buying/selling at market price:
                - Buying: qty should be input in USDT units (e.g., "10" = 10 USDT)
                - Selling: qty should be input in BTC units (e.g., "0.000100" = 0.0001 BTC)
            3. Futures trading requires positionIdx:
                - Long position: positionIdx=1
                - Short position: positionIdx=2
            4. positionIdx is not used for spot trading

        Reference site:
            https://bybit-exchange.github.io/docs/v5/order/create-order
        """
        try:
            # Default settings
            if timeInForce is None:
                timeInForce = "IOC" if orderType == "Market" else "GTC"
            if orderFilter is None:
                orderFilter = "Order"
            if isLeverage is None:
                isLeverage = 0

            # Check positionIdx for futures trading
            if category in ["linear", "inverse"]:
                if not positionIdx or positionIdx not in ["1", "2"]:
                    return {"error": "positionIdx is required for futures trading (1: Long position, 2: Short position)"}
            
            # Ignore positionIdx for spot trading
            if category == "spot":
                positionIdx = None

            # Prepare request data
            request_data = {
                "category": category,
                "symbol": symbol,
                "side": side,
                "orderType": orderType,
                "qty": qty,
                "timeInForce": timeInForce,
                "orderFilter": orderFilter,
                "isLeverage": isLeverage
            }

            # Add optional parameters
            if price is not None:
                request_data["price"] = price
            if orderLinkId is not None:
                request_data["orderLinkId"] = orderLinkId
            if triggerPrice is not None:
                request_data["triggerPrice"] = triggerPrice
            if triggerBy is not None:
                request_data["triggerBy"] = triggerBy
            if orderIv is not None:
                request_data["orderIv"] = orderIv
            if positionIdx is not None:
                request_data["positionIdx"] = positionIdx
            if takeProfit is not None:
                request_data["takeProfit"] = takeProfit
            if stopLoss is not None:
                request_data["stopLoss"] = stopLoss
            if tpTriggerBy is not None:
                request_data["tpTriggerBy"] = tpTriggerBy
            if slTriggerBy is not None:
                request_data["slTriggerBy"] = slTriggerBy
            if tpLimitPrice is not None:
                request_data["tpLimitPrice"] = tpLimitPrice
            if slLimitPrice is not None:
                request_data["slLimitPrice"] = slLimitPrice
            if tpOrderType is not None:
                request_data["tpOrderType"] = tpOrderType
            if slOrderType is not None:
                request_data["slOrderType"] = slOrderType

            # Execute order
            result = self.client.place_order(**request_data)

            # Check minimum order quantity/amount
            if isinstance(result, dict) and "error" in result:
                if "min_qty" in result and "min_amt" in result:
                    # Minimum order quantity/amount verification failed
                    logger.error(f"Order execution failed: {result['error']}")
                    return {
                        "error": f"{result['error']} (Minimum order quantity: {result['min_qty']} {symbol.replace('USDT', '')}, Minimum order amount: {result['min_amt']} USDT)"
                    }
                else:
                    logger.error(f"Order execution failed: {result['error']}")
                    return {"error": result['error']}
            elif result.get("retCode") != 0:
                logger.error(f"Order execution failed: {result.get('retMsg')}")
                return {"error": result.get("retMsg")}
            return result
        except Exception as e:
            logger.error(f"Order execution failed: {e}", exc_info=True)
            return {"error": str(e)}

    def cancel_order(self, category: str, symbol: str, orderId: Optional[str] = None,
                     orderLinkId: Optional[str] = None, orderFilter: Optional[str] = None) -> Dict:
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
        """
        return self.client.cancel_order(
            category=category,
            symbol=symbol,
            orderId=orderId,
            orderLinkId=orderLinkId,
            orderFilter=orderFilter
        )

    def get_order_history(self, category: str, symbol: Optional[str] = None,
                          orderId: Optional[str] = None, orderLinkId: Optional[str] = None,
                          orderFilter: Optional[str] = None, orderStatus: Optional[str] = None,
                          startTime: Optional[int] = None, endTime: Optional[int] = None,
                          limit: int = 50) -> Dict:
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
        """
        return self.client.get_order_history(
            category=category,
            symbol=symbol,
            orderId=orderId,
            orderLinkId=orderLinkId,
            orderFilter=orderFilter,
            orderStatus=orderStatus,
            startTime=startTime,
            endTime=endTime,
            limit=limit
        )

    def get_open_orders(self, category: str, symbol: Optional[str] = None,
                        orderId: Optional[str] = None, orderLinkId: Optional[str] = None,
                        orderFilter: Optional[str] = None, limit: int = 50) -> Dict:
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
        """
        return self.client.get_open_orders(
            category=category,
            symbol=symbol,
            orderId=orderId,
            orderLinkId=orderLinkId,
            orderFilter=orderFilter,
            limit=limit
        )

    # Leverage related methods
    def set_leverage(self, category: str, symbol: str, buyLeverage: str,
                     sellLeverage: str) -> Dict:
        """
        Set leverage

        Args:
            category (str): Category (spot, linear, inverse, etc.)
            symbol (str): Symbol (e.g., BTCUSDT)
            buyLeverage (str): Buy leverage
            sellLeverage (str): Sell leverage

        Returns:
            Dict: Setting result
        """
        return self.client.set_leverage(
            category=category,
            symbol=symbol,
            buyLeverage=buyLeverage,
            sellLeverage=sellLeverage
        )

    def set_trading_stop(self, category: str, symbol: str,
                         takeProfit: Optional[str] = None,
                         stopLoss: Optional[str] = None,
                         trailingStop: Optional[str] = None,
                         positionIdx: Optional[int] = None) -> Dict:
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
        """
        return self.client.set_trading_stop(
            category=category,
            symbol=symbol,
            takeProfit=takeProfit,
            stopLoss=stopLoss,
            trailingStop=trailingStop,
            positionIdx=positionIdx
        )

    def set_margin_mode(self, category: str, symbol: str,
                        tradeMode: int, buyLeverage: str,
                        sellLeverage: str) -> Dict:
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
        """
        return self.client.set_margin_mode(
            category=category,
            symbol=symbol,
            tradeMode=tradeMode,
            buyLeverage=buyLeverage,
            sellLeverage=sellLeverage
        )

    # Utility methods
    def get_api_key_information(self) -> Dict:
        """
        Get API key information

        Returns:
            Dict: API key information
        """
        return self.client.get_api_key_information()

    def get_instruments_info(self, category: str, symbol: str,
                             status: Optional[str] = None, baseCoin: Optional[str] = None) -> Dict:
        """
        Get exchange information

        Args:
            category (str): Category (spot, linear, inverse, etc.)
            symbol (str): Symbol (e.g., BTCUSDT)
            status (Optional[str]): Status
            baseCoin (Optional[str]): Base coin

        Returns:
            Dict: Exchange information
        """
        return self.client.get_instruments_info(
            category=category,
            symbol=symbol,
            status=status,
            baseCoin=baseCoin
        )


if __name__ == "__main__":
    # Example usage
    bybit_service = BybitService()
    # orderbook = bybit_service.get_orderbook(category='spot', symbol='BTCUSDT')
    # {
    #     "category": "spot",
    #     "symbol": "BTCUSDT",
    #     "interval": "1",
    #     "limit": 10
    # }
    orderbook = bybit_service.get_kline(
        category='spot',
        symbol='BTCUSDT',
        interval='1',
        start=1699996800000,
        end=1700083200000,
        limit=10
    )

    data = bybit_service.get_talib_kline(
        category='spot',
        symbol='BTCUSDT',
        interval='1',
        start=1699996800000,
        end=1700083200000,
        limit=50,
        indicators={
            'SMA': [5, 10],
            'EMA': [10],
            'RSI': [{'timeperiod': 14}],
            'MACD': [{'fastperiod': 12, 'slowperiod': 26, 'signalperiod': 9}]
        }
    )
    print(orderbook)