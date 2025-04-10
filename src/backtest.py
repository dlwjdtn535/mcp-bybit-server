from datetime import datetime
import pandas as pd
from typing import Dict, Any
import logging
import talib

from service import BybitService
from state import BacktestState

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create BybitService instance
bybit_service = BybitService()

def run_strategy(
    start_time: int,
    end_time: int,
    strategy_vars: Dict[str, Any]
) -> Dict:
    """
    Run backtest strategy

    Args:
        start_time: Backtest start time (millisecond timestamp)
        end_time: Backtest end time (millisecond timestamp)
        strategy_vars: Strategy variables dictionary

    Returns:
        Dict: Backtest results
    """
    logger.info(f"Starting backtest: {datetime.fromtimestamp(start_time/1000)} ~ {datetime.fromtimestamp(end_time/1000)}")
    logger.info(f"Strategy variables: {strategy_vars}")

    try:
        # Fetch data
        data = bybit_service.get_kline(
            category='spot',
            symbol='BTCUSDT',
            interval='1',
            start=start_time,
            end=end_time,
            limit=1440  # 24 hours * 60 minutes
        )

        if not data or 'result' not in data or 'list' not in data['result']:
            return {
                'error': 'Failed to load data'
            }

        # Create DataFrame
        df = pd.DataFrame(data['result']['list'], columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'
        ])

        # Data preprocessing
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        df = df.sort_index()

        for col in ['open', 'high', 'low', 'close', 'volume', 'turnover']:
            df[col] = df[col].astype(float)

        # Calculate RSI
        df['RSI'] = talib.RSI(df['close'].values, timeperiod=14)

        logger.info(f"Data loaded: {len(df)} candles")

        # Initialize backtest state
        initial_balance = strategy_vars.get('initial_balance', {'USDT': 10000.0, 'BTC': 0.0})
        backtest = BacktestState()
        backtest.initialize_backtest(start_time, end_time, initial_balance)

        # Set strategy variables
        rsi_config = strategy_vars['indicators']['rsi']
        position_config = strategy_vars['position']

        rsi_buy_threshold = rsi_config['buy_threshold']
        profit_target = position_config['profit_target']
        stop_loss = position_config['stop_loss']
        position_size = position_config['size']

        # Execute strategy for each candle
        trades = []
        for i in range(len(df)):
            current_row = df.iloc[i]
            current_time = current_row.name
            current_price = current_row['close']
            current_rsi = current_row['RSI']

            if pd.isna(current_rsi):
                continue

            # Check buy signal
            if not backtest.position['in_position']:
                if current_rsi <= rsi_buy_threshold:
                    # Calculate buy quantity
                    available_usdt = backtest.current_balance['USDT']
                    trade_amount = available_usdt * (position_size / 100)
                    quantity = round(trade_amount / current_price, 8)

                    if quantity > 0:
                        backtest.execute_trade(current_time, 'buy', current_price, quantity)
                        logger.info(f"Buy: time={current_time}, price={current_price}, RSI={current_rsi:.2f}")
                        trades.append({
                            'time': current_time,
                            'type': 'buy',
                            'price': current_price,
                            'quantity': quantity,
                            'rsi': current_rsi
                        })

            # Check sell signal
            elif backtest.position['in_position']:
                entry_price = backtest.position['entry_price']
                current_return = (current_price - entry_price) / entry_price * 100

                # Take profit condition
                if current_return >= profit_target:
                    quantity = backtest.position['quantity']
                    backtest.execute_trade(current_time, 'sell', current_price, quantity)
                    logger.info(f"Take profit: time={current_time}, price={current_price}, return={current_return:.2f}%")
                    trades.append({
                        'time': current_time,
                        'type': 'sell',
                        'price': current_price,
                        'quantity': quantity,
                        'return': current_return,
                        'reason': 'take_profit'
                    })

                # Stop loss condition
                elif current_return <= stop_loss:
                    quantity = backtest.position['quantity']
                    backtest.execute_trade(current_time, 'sell', current_price, quantity)
                    logger.info(f"Stop loss: time={current_time}, price={current_price}, loss={current_return:.2f}%")
                    trades.append({
                        'time': current_time,
                        'type': 'sell',
                        'price': current_price,
                        'quantity': quantity,
                        'return': current_return,
                        'reason': 'stop_loss'
                    })

        # Backtest results
        results = backtest.get_results()
        results['trades'] = trades

        logger.info("Backtest completed")
        logger.info(f"Total trades: {len(trades)}")
        logger.info(f"Final balance: {backtest.current_balance}")

        return results

    except Exception as e:
        logger.error(f"Error during backtest execution: {str(e)}")
        return {'error': f'Backtest error: {str(e)}'}

def check_buy_signals(row: pd.Series, indicators: Dict) -> bool:
    """매수 신호 확인"""
    signals = []

    # RSI
    if 'rsi' in indicators:
        rsi_config = indicators['rsi']
        if 'buy_threshold' in rsi_config and 'RSI_14' in row:
            signals.append(row['RSI_14'] < rsi_config['buy_threshold'])

    # MFI
    if 'mfi' in indicators:
        mfi_config = indicators['mfi']
        if 'buy_threshold' in mfi_config and 'MFI_14' in row:
            signals.append(row['MFI_14'] < mfi_config['buy_threshold'])

    # 볼린저 밴드
    if 'bollinger' in indicators:
        if 'BBANDS_LOWER' in row:
            signals.append(row['close'] < row['BBANDS_LOWER'])

    # SMA 크로스
    if 'sma' in indicators:
        sma_periods = indicators['sma']['periods']
        if len(sma_periods) >= 2:
            short_sma = f'SMA_{sma_periods[0]}'
            long_sma = f'SMA_{sma_periods[1]}'
            if short_sma in row and long_sma in row:
                signals.append(row[short_sma] > row[long_sma])  # 골든 크로스

    # EMA 크로스
    if 'ema' in indicators:
        ema_periods = indicators['ema']['periods']
        if len(ema_periods) >= 2:
            short_ema = f'EMA_{ema_periods[0]}'
            long_ema = f'EMA_{ema_periods[1]}'
            if short_ema in row and long_ema in row:
                signals.append(row[short_ema] > row[long_ema])  # 골든 크로스

    # 모든 지표의 매수 신호가 True일 때만 매수
    return all(signals) if signals else False

def check_sell_signals(row: pd.Series, indicators: Dict) -> bool:
    """매도 신호 확인"""
    signals = []

    # RSI
    if 'rsi' in indicators:
        rsi_config = indicators['rsi']
        if 'sell_threshold' in rsi_config and 'RSI_14' in row:
            signals.append(row['RSI_14'] > rsi_config['sell_threshold'])

    # MFI
    if 'mfi' in indicators:
        mfi_config = indicators['mfi']
        if 'sell_threshold' in mfi_config and 'MFI_14' in row:
            signals.append(row['MFI_14'] > mfi_config['sell_threshold'])

    # 볼린저 밴드
    if 'bollinger' in indicators:
        if 'BBANDS_UPPER' in row:
            signals.append(row['close'] > row['BBANDS_UPPER'])

    # SMA 크로스
    if 'sma' in indicators:
        sma_periods = indicators['sma']['periods']
        if len(sma_periods) >= 2:
            short_sma = f'SMA_{sma_periods[0]}'
            long_sma = f'SMA_{sma_periods[1]}'
            if short_sma in row and long_sma in row:
                signals.append(row[short_sma] < row[long_sma])  # 데드 크로스

    # EMA 크로스
    if 'ema' in indicators:
        ema_periods = indicators['ema']['periods']
        if len(ema_periods) >= 2:
            short_ema = f'EMA_{ema_periods[0]}'
            long_ema = f'EMA_{ema_periods[1]}'
            if short_ema in row and long_ema in row:
                signals.append(row[short_ema] < row[long_ema])  # 데드 크로스

    # 하나의 매도 신호라도 있으면 매도
    return any(signals) if signals else False

if __name__ == "__main__":
    # Test strategy variables
    strategy_vars = {
        'initial_balance': {
            'USDT': 1000.0,
            'BTC': 0.0
        },
        'indicators': {
            'rsi': {
                'period': 14,
                'buy_threshold': 30
            }
        },
        'position': {
            'size': 100,
            'profit_target': 0.3,
            'stop_loss': -0.3
        }
    }

    # Set backtest period
    start_time = int(datetime(2025, 4, 1).timestamp() * 1000)
    end_time = int(datetime(2025, 4, 4, 23, 59, 59).timestamp() * 1000)

    # Run backtest
    results = run_strategy(start_time, end_time, strategy_vars)
    print("Backtest results:", results)