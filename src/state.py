from datetime import datetime
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any

class BacktestState:
    def __init__(self):
        # Backtesting configuration
        self.start_time: Optional[int] = None  # Timestamp in milliseconds
        self.end_time: Optional[int] = None    # Timestamp in milliseconds
        self.symbol: str = 'BTCUSDT'           # Default trading pair
        self.timeframe: str = '1'              # Default timeframe (1 minute)
        
        # Historical data
        self.historical_data: pd.DataFrame = pd.DataFrame()  # Price data with indicators
        
        # Account state
        self.initial_balance: Dict[str, float] = {
            'USDT': 10000.0,  # Default initial balance
            'BTC': 0.0
        }
        self.current_balance: Dict[str, float] = self.initial_balance.copy()
        
        # Position tracking
        self.position: Dict = {
            'in_position': False,
            'entry_price': 0.0,
            'quantity': 0.0,
            'side': None  # 'long' or 'short'
        }
        
        # Trade history
        self.trades: List[Dict] = []
        
        # Performance metrics
        self.metrics: Dict = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'total_profit_loss': 0.0,
            'profit_factor': 0.0,
            'max_drawdown': 0.0,
            'max_drawdown_percentage': 0.0,
            'total_profit_percentage': 0.0,
            'average_profit_per_trade': 0.0,
            'average_win': 0.0,
            'average_loss': 0.0,
            'largest_win': 0.0,
            'largest_loss': 0.0,
            'max_consecutive_wins': 0,
            'max_consecutive_losses': 0
        }

        # Strategy variables
        self.strategy_vars: Dict[str, Any] = {}

    def set_strategy_var(self, var_name: str, value: Any) -> None:
        """
        Set strategy variable
        
        Args:
            var_name: Variable name
            value: Variable value
        """
        self.strategy_vars[var_name] = value

    def get_strategy_var(self, var_name: str, default: Any = None) -> Any:
        """
        Get strategy variable
        
        Args:
            var_name: Variable name
            default: Default value (returned if variable doesn't exist)
            
        Returns:
            Strategy variable value
        """
        return self.strategy_vars.get(var_name, default)

    def remove_strategy_var(self, var_name: str) -> None:
        """
        Remove strategy variable
        
        Args:
            var_name: Variable name
        """
        if var_name in self.strategy_vars:
            del self.strategy_vars[var_name]

    def clear_strategy_vars(self) -> None:
        """Clear all strategy variables"""
        self.strategy_vars.clear()

    def initialize_backtest(self, start_time: int, end_time: int, initial_balance: Optional[Dict[str, float]] = None) -> None:
        """
        Initialize backtest
        
        Args:
            start_time: Start time (millisecond timestamp)
            end_time: End time (millisecond timestamp)
            initial_balance: Initial balance (default: {'USDT': 10000.0, 'BTC': 0.0})
        """
        self.start_time = start_time
        self.end_time = end_time
        if initial_balance:
            self.initial_balance = initial_balance.copy()
            self.current_balance = initial_balance.copy()
        self._reset_metrics()
        self.clear_strategy_vars()

    def _reset_metrics(self) -> None:
        """Reset performance metrics"""
        self.trades = []
        self.position = {
            'in_position': False,
            'entry_price': 0.0,
            'quantity': 0.0,
            'side': None
        }
        self.metrics = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'total_profit_loss': 0.0,
            'profit_factor': 0.0,
            'max_drawdown': 0.0,
            'max_drawdown_percentage': 0.0,
            'total_profit_percentage': 0.0,
            'average_profit_per_trade': 0.0,
            'average_win': 0.0,
            'average_loss': 0.0,
            'largest_win': 0.0,
            'largest_loss': 0.0,
            'max_consecutive_wins': 0,
            'max_consecutive_losses': 0
        }

    def load_historical_data(self, data: List[Dict]) -> None:
        """
        Load and preprocess historical data
        
        Args:
            data: Historical data list from API
        """
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        df = df.sort_index()
        
        # Calculate technical indicators
        self._calculate_indicators(df)
        self.historical_data = df

    def _calculate_indicators(self, df: pd.DataFrame) -> None:
        """
        Calculate technical indicators
        
        Args:
            df: DataFrame with price data
        """
        # Set RSI period
        rsi_period = self.get_strategy_var('rsi_period', 14)
        
        # Set SMA periods
        sma_periods = self.get_strategy_var('sma_periods', [20, 50])
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # SMA
        for period in sma_periods:
            df[f'sma{period}'] = df['close'].rolling(window=period).mean()

    def execute_trade(self, timestamp: datetime, side: str, price: float, quantity: float) -> None:
        """
        Execute and record trade
        
        Args:
            timestamp: Trade time
            side: Trade direction ('buy' or 'sell')
            price: Trade price
            quantity: Trade quantity
        """
        trade = {
            'timestamp': timestamp,
            'side': side,
            'price': price,
            'quantity': quantity,
            'value': price * quantity
        }
        
        if side.lower() == 'buy':
            cost = trade['value']
            if self.current_balance['USDT'] >= cost:
                self.current_balance['USDT'] -= cost
                self.current_balance['BTC'] += quantity
                self.position = {
                    'in_position': True,
                    'entry_price': price,
                    'quantity': quantity,
                    'side': 'long'
                }
                self.trades.append(trade)
        
        elif side.lower() == 'sell' and self.position['in_position']:
            revenue = trade['value']
            self.current_balance['USDT'] += revenue
            self.current_balance['BTC'] -= quantity
            
            # Calculate profit/loss
            profit_loss = (price - self.position['entry_price']) * quantity
            trade['profit_loss'] = profit_loss
            trade['profit_loss_percentage'] = (profit_loss / (self.position['entry_price'] * quantity)) * 100
            
            self.position = {
                'in_position': False,
                'entry_price': 0.0,
                'quantity': 0.0,
                'side': None
            }
            self.trades.append(trade)
            self._update_metrics(trade)

    def _update_metrics(self, trade: Dict) -> None:
        """
        Update performance metrics after trade
        
        Args:
            trade: Trade information
        """
        self.metrics['total_trades'] += 1
        
        if trade['profit_loss'] > 0:
            self.metrics['winning_trades'] += 1
            self.metrics['average_win'] = ((self.metrics['average_win'] * (self.metrics['winning_trades'] - 1)) + 
                                         trade['profit_loss']) / self.metrics['winning_trades']
            self.metrics['largest_win'] = max(self.metrics['largest_win'], trade['profit_loss'])
        else:
            self.metrics['losing_trades'] += 1
            self.metrics['average_loss'] = ((self.metrics['average_loss'] * (self.metrics['losing_trades'] - 1)) + 
                                          trade['profit_loss']) / self.metrics['losing_trades']
            self.metrics['largest_loss'] = min(self.metrics['largest_loss'], trade['profit_loss'])

        self.metrics['total_profit_loss'] += trade['profit_loss']
        self.metrics['win_rate'] = (self.metrics['winning_trades'] / self.metrics['total_trades']) * 100
        self.metrics['average_profit_per_trade'] = self.metrics['total_profit_loss'] / self.metrics['total_trades']
        self.metrics['total_profit_percentage'] = (self.metrics['total_profit_loss'] / self.initial_balance['USDT']) * 100

    def get_results(self) -> Dict:
        """
        Get backtest results
        
        Returns:
            Dict: Backtest results and performance metrics
        """
        return {
            'initial_balance': self.initial_balance,
            'final_balance': self.current_balance,
            'metrics': self.metrics,
            'trades': self.trades,
            'strategy_vars': self.strategy_vars
        }

    def print_results(self) -> None:
        """Print backtest results"""
        print("\n=== Backtest Results ===")
        print(f"Initial Balance: {self.initial_balance}")
        print(f"Final Balance: {self.current_balance}")
        print(f"\n=== Strategy Variables ===")
        for var_name, value in self.strategy_vars.items():
            print(f"{var_name}: {value}")
        print(f"\n=== Trading Metrics ===")
        print(f"Total Trades: {self.metrics['total_trades']}")
        print(f"Win Rate: {self.metrics['win_rate']:.2f}%")
        print(f"Total Profit: {self.metrics['total_profit_loss']:.2f} USDT")
        print(f"Return: {self.metrics['total_profit_percentage']:.2f}%")
        print(f"Average Profit per Trade: {self.metrics['average_profit_per_trade']:.2f} USDT")
        print(f"Largest Win: {self.metrics['largest_win']:.2f} USDT")
        print(f"Largest Loss: {self.metrics['largest_loss']:.2f} USDT")
        print(f"Average Win: {self.metrics['average_win']:.2f} USDT")
        print(f"Average Loss: {self.metrics['average_loss']:.2f} USDT") 