import blankly
import requests

from blankly.data import PriceReader


def price_event(price, symbol, state: blankly.StrategyState):
    """
    Implements a moving average crossover strategy:
    - Buy when fast MA crosses above slow MA (golden cross)
    - Sell when fast MA crosses below slow MA (death cross)
    """
    # Add current price to history
    state.variables["history"].append(price)

    # Calculate fast (20-period) and slow (50-period) moving averages
    fast_ma = blankly.indicators.sma(state.variables["history"], period=20)
    slow_ma = blankly.indicators.sma(state.variables["history"], period=50)

    # Need at least 50 periods of data for both MAs
    if len(fast_ma) < 2 or len(slow_ma) < 2:
        return

    # Get current position
    curr_value = state.interface.account[state.base_asset].available

    # Check for golden cross (fast MA crosses above slow MA)
    if fast_ma[-1] > slow_ma[-1] and fast_ma[-2] <= slow_ma[-2] and not curr_value:
        # Calculate buy amount based on available cash
        buy_size = state.interface.cash / price
        # Place market buy order
        state.interface.market_order(symbol, side="buy", size=buy_size)

    # Check for death cross (fast MA crosses below slow MA)
    elif fast_ma[-1] < slow_ma[-1] and fast_ma[-2] >= slow_ma[-2] and curr_value:
        # Sell entire position
        state.interface.market_order(symbol, side="sell", size=curr_value)


def init(symbol, state: blankly.StrategyState):
    # Download price data to give context to the algo
    state.variables["history"] = state.interface.history(
        symbol, to=150, return_as="deque", resolution=state.resolution
    )["close"]


import pandas as pd
from datetime import datetime


def transform_csv(input_file, output_file):
    """
    Transform CSV from the input format to the target format.

    Args:
        input_file (str): Path to input CSV file
        output_file (str): Path to output CSV file
    """
    # Read the input CSV
    df = pd.read_csv(input_file)

    # Create new dataframe with required columns
    new_df = pd.DataFrame(
        {
            "time": df["start"].apply(
                lambda x: int(x / 1000)
            ),  # Convert milliseconds to seconds
            "low": df["fillLow"],  # Using fill values instead of oracle values
            "high": df["fillHigh"],
            "open": df["fillOpen"],
            "close": df["fillClose"],
            "volume": df[
                "baseVolume"
            ],  # Using base volume as it's likely the asset volume
        }
    )

    # Reset index to add the numeric index column
    new_df = new_df.reset_index(drop=True)

    # Save to CSV
    new_df.to_csv(output_file)


# Example usage:
# transform_csv('input.csv', 'output.csv')

if __name__ == "__main__":

    # data = requests.get(
    #     "https://firebasestorage.googleapis.com/v0/b/blankly-6ada5.appspot.com/o/demo_data.csv?alt=media&token=acfa5c39-8f08-45dc-8be3-2033dc2b7b28"
    # ).text
    # with open("./price_examples.csv", "w") as file:
    #     file.write(data)

    # stransform_csv("./15.csv", "./15_transformed.csv")

    # Run on the keyless exchange, starting at 100k
    exchange = blankly.KeylessExchange(
        price_reader=PriceReader("./15_transformed.csv", "BTC-USD")
    )

    # Use our strategy helper
    strategy = blankly.Strategy(exchange)

    # Make the price event function above run every day
    strategy.add_price_event(price_event, symbol="BTC-USD", resolution="15m", init=init)

    # Backtest the strategy
    results = strategy.backtest(
        start_date=1704067200, end_date=1733442300, initial_values={"USD": 10000}
    )
    print(results)
