import pandas as pd
import numpy as np
from datetime import datetime


# Helper functions for performance metrics
def calculate_cumulative_return(positions):
    return (positions["PnL"].sum() / positions["Entry Price"].sum()) * 100


def calculate_annualized_return(positions, trading_days=252):
    total_return = calculate_cumulative_return(positions)
    total_days = (positions["Exit Time"].max() - positions["Entry Time"].min()).days
    annualized_return = ((1 + total_return) ** (trading_days / total_days)) - 1
    return annualized_return


def calculate_sharpe_ratio(positions, risk_free_rate=0.01):
    returns = positions["PnL"] / positions["Entry Price"]
    excess_returns = returns - risk_free_rate / 252
    sharpe_ratio = np.mean(excess_returns) / np.std(excess_returns)
    return sharpe_ratio


def calculate_sortino_ratio(positions, risk_free_rate=0.01):
    returns = positions["PnL"] / positions["Entry Price"]
    downside_returns = returns[returns < 0]
    downside_risk = np.sqrt(np.mean(downside_returns**2))
    sortino_ratio = (np.mean(returns) - risk_free_rate / 252) / downside_risk
    return sortino_ratio


def calculate_win_rate(positions):
    wins = positions[positions["PnL"] > 0].shape[0]
    total = positions.shape[0]
    return wins / total


from typing import Dict, Optional, Union
import pandas as pd
from datetime import datetime


# def rsi_trend_following_strategy(
#     window_data: pd.DataFrame, positions: pd.DataFrame
# ) -> Optional[Dict[str, Union[int, float, datetime]]]:
#     """
#     RSI Trend Following Strategy

#     Args:
#         window_data (pd.DataFrame): Historical price data with columns ['start', 'fillOpen']
#         positions (pd.DataFrame): Current open positions

#     Returns:
#         Optional[Dict[str, Union[int, float, datetime]]]: Trade signal with entry details or None
#             {
#                 'Size': int,          # 1 for long, -1 for short
#                 'Entry Time': datetime,# Entry timestamp
#                 'Entry Price': float  # Entry price
#             }
#     """
#     rsi_period = 14
#     overbought = 70
#     oversold = 30

#     if len(window_data) >= rsi_period:
#         # Calculate price changes
#         delta = window_data["fillOpen"].diff()

#         # Calculate gains and losses
#         gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
#         loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()

#         # Calculate RSI
#         rs = gain / loss
#         rsi = 100 - (100 / (1 + rs))

#         last_row = window_data.iloc[-1]

#         # Check for buy signal
#         if rsi.iloc[-1] < oversold:
#             return {
#                 "Size": 1,  # Long position
#                 "Entry Time": last_row["start"],
#                 "Entry Price": last_row["fillOpen"],
#             }

#         # Check for sell signal
#         elif rsi.iloc[-1] > overbought:
#             return {
#                 "Size": -1,  # Short position
#                 "Entry Time": last_row["start"],
#                 "Entry Price": last_row["fillOpen"],
#             }

#     return None


def example_strategy(window_data, positions):
    fast_ma = 10
    slow_ma = 30

    if len(window_data) >= slow_ma:
        # Calculate moving averages
        fast_ma_current = window_data["fillOpen"][-fast_ma:].mean()
        slow_ma_current = window_data["fillOpen"][-slow_ma:].mean()

        # Calculate previous day's moving averages
        fast_ma_prev = window_data["fillOpen"][-fast_ma - 1 : -1].mean()
        slow_ma_prev = window_data["fillOpen"][-slow_ma - 1 : -1].mean()

        last_row = window_data.iloc[-1]

        # Check for Golden Cross (fast MA crosses above slow MA)
        if fast_ma_prev <= slow_ma_prev and fast_ma_current > slow_ma_current:
            return {
                "Size": 1,  # Long position
                "Entry Time": last_row["start"],
                "Entry Price": last_row["fillOpen"],
            }

        # Check for Death Cross (fast MA crosses below slow MA)
        elif fast_ma_prev >= slow_ma_prev and fast_ma_current < slow_ma_current:
            return {
                "Size": -1,  # Short position
                "Entry Time": last_row["start"],
                "Entry Price": last_row["fillOpen"],
            }

    return None


def backtest_strategy(candle_file, strategy_function=example_strategy):
    # Load candle data with proper timestamp parsing
    candle_data = pd.read_csv(candle_file)
    # Convert Unix timestamp (assuming milliseconds) to datetime
    candle_data["start"] = pd.to_datetime(candle_data["start"], unit="ms")

    # Initialize positions DataFrame
    positions = pd.DataFrame(
        {
            "Size": pd.Series(dtype="float"),
            "Entry Time": pd.Series(dtype="datetime64[ms]"),
            "Entry Price": pd.Series(dtype="float"),
            "Exit Time": pd.Series(dtype="datetime64[ms]"),
            "Exit Price": pd.Series(dtype="float"),
            "PnL": pd.Series(dtype="float"),
        }
    )
    # walk ahead with a growing window
    for i in range(1, len(candle_data) + 1):
        # Get the data up to index i (growing window)
        window_data = candle_data.iloc[:i]

        position = strategy_function(window_data, positions)

        if position:
            if position["Size"] < 0:
                positions_to_close = positions[
                    (positions["Size"] > 0) & (positions["Exit Time"].isna())
                ]
            else:
                positions_to_close = positions[
                    (positions["Size"] < 0) & (positions["Exit Time"].isna())
                ]

            if len(positions_to_close) > 0:
                # Get the index of the last position to close
                idx = positions_to_close.index[-1]

                # Use .loc to modify the original DataFrame
                positions.loc[idx, "Exit Time"] = window_data.iloc[-1]["start"]
                positions.loc[idx, "Exit Price"] = window_data.iloc[-1]["fillOpen"]
                positions.loc[idx, "PnL"] = (
                    positions.loc[idx, "Exit Price"] - positions.loc[idx, "Entry Price"]
                ) * positions.loc[idx, "Size"]
            else:
                new_position = pd.DataFrame([position])
                positions = pd.concat([positions, new_position], ignore_index=True)

    closed_positions_only = positions[positions["Exit Time"].notna()]

    # Calculate metrics
    metrics = {
        "Cumulative Return": calculate_cumulative_return(closed_positions_only),
        "Annualized Return": calculate_annualized_return(closed_positions_only),
        "Sharpe Ratio": calculate_sharpe_ratio(closed_positions_only),
        "Sortino Ratio": calculate_sortino_ratio(closed_positions_only),
        "Win Rate": calculate_win_rate(closed_positions_only),
        "Number of positions": closed_positions_only.shape[0],
    }

    return metrics, positions


# # Example usage
# candle_file = "./data/perp_BTC_15_2024.csv"  # Path to your candle data file
# metrics, positions = backtest_strategy(candle_file, rsi_trend_following_strategy)
# print(metrics)
