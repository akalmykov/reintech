from langchain_core.tools import BaseTool
from typing import Dict, Optional, Union
import pandas as pd
import importlib.util
import sys
import os
from datetime import datetime
import asyncio
from pydantic import Field

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.backtesting_engine import backtest_strategy


class BacktestingTool(BaseTool):
    name: str = "BacktestingTool"
    description: str = """Use this tool to backtest a trading strategy on historical data.
    Inputs are the strategy code and the historical candle data file:
    - 'strategy_code': Python code of the strategy function as string
    - 'data_file': Path to the CSV file with historical data
    The strategy function should follow this template:
    def strategy(window_data: pd.DataFrame, positions: pd.DataFrame) -> Optional[Dict[str, Union[int, float, datetime]]]
    """

    def _load_strategy(self, strategy_code: str) -> callable:
        """Dynamically load strategy function from string code."""
        try:
            # Create a temporary module
            spec = importlib.util.spec_from_loader("strategy_module", loader=None)
            module = importlib.util.module_from_spec(spec)
            sys.modules["strategy_module"] = module

            # Execute the strategy code in the module's context
            exec(strategy_code, module.__dict__)

            # Return the strategy function
            return module.strategy
        except Exception as e:
            raise ValueError(f"Error loading strategy: {str(e)}")

    strategy_code: str = Field(..., description="Python code of the strategy function")
    data_file: str = Field(..., description="Path to the historical data CSV file")

    def __init__(self, strategy_code: str, data_file: str):
        super().__init__(strategy_code=strategy_code, data_file=data_file)

    def _run(self, tool_input: str) -> str:
        """Run backtest using the stored strategy code and data file.

        Returns:
            str: JSON string with backtest results
        """
        try:

            if not self.strategy_code or not self.data_file:
                return "Error: Both strategy_code and data_file are required"

            # Load the strategy function
            strategy_fn = self._load_strategy(self.strategy_code)

            metrics, positions = backtest_strategy(self.data_file, strategy_fn)
            return str(metrics)

        except Exception as e:
            return f"Error running backtest: {str(e)}"

    async def _arun(self, tool_input: str) -> str:
        """Async version of _run"""
        return self._run(tool_input)


# Example usage:
async def main():

    sample_strategy_code = """
from typing import Dict, Optional, Union
import pandas as pd
from datetime import datetime

def strategy(
    window_data: pd.DataFrame, positions: pd.DataFrame
) -> Optional[Dict[str, Union[int, float, datetime]]]:
    \"""
    RSI Trend Following Strategy

    Args:
        window_data (pd.DataFrame): Historical price data with columns ['start', 'fillOpen']
        positions (pd.DataFrame): Current open positions

    Returns:
        Optional[Dict[str, Union[int, float, datetime]]]: Trade signal with entry details or None
            {
                'Size': int,          # 1 for long, -1 for short
                'Entry Time': datetime,# Entry timestamp
                'Entry Price': float  # Entry price
            }
    \"""
    rsi_period = 14
    overbought = 70
    oversold = 30

    if len(window_data) >= rsi_period:
        # Calculate price changes
        delta = window_data["fillOpen"].diff()

        # Calculate gains and losses
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()

        # Calculate RSI
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        last_row = window_data.iloc[-1]

        # Check for buy signal
        if rsi.iloc[-1] < oversold:
            return {
                "Size": 1,  # Long position
                "Entry Time": last_row["start"],
                "Entry Price": last_row["fillOpen"],
            }

        # Check for sell signal
        elif rsi.iloc[-1] > overbought:
            return {
                "Size": -1,  # Short position
                "Entry Time": last_row["start"],
                "Entry Price": last_row["fillOpen"],
            }

    return None
    """
    print(sample_strategy_code)
    # Run the backtest
    backtest_tool = BacktestingTool(sample_strategy_code, "./data/perp_BTC_15_2024.csv")

    result = await backtest_tool.arun("")
    print(result)


if __name__ == "__main__":
    # Run example
    # asyncio.run(main())
    pass
