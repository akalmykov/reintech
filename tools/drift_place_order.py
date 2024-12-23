from langchain_core.tools import BaseTool
import json
import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from driftpy.types import PositionDirection, OrderParams, OrderType
from tools.drift_interface import place_order, init, shutdown
from tools.drift_constants import drift_perp_markets_dict


class DriftOrderTool(BaseTool):
    name: str = "DriftOrderTool"
    description: str = """Use this tool to place orders on Drift Exchange.
    Input should be a JSON string containing:
    - 'amount': float (amount to trade)
    - 'direction': string ('long' or 'short')
    - 'symbol': symbol/ticker to trade (e.g. SOL)
    Example: amount 0.1, direction: "long", symbol: ETH
    This tool returns the transaction signature on successful execution.
    """

    def _run(self, amount: float, direction: str, symbol: str) -> str:
        """Place an order on Drift Exchange."""
        try:

            market_index = drift_perp_markets_dict[symbol]["marketIndex"]
            sub_account_id = 0

            if not amount:
                return "Error: Amount is required"

            # Convert direction string to PositionDirection
            direction = (
                PositionDirection.Long()
                if direction.lower() == "long"
                else PositionDirection.Short()
            )

            # Run the order placement
            tx_sig = asyncio.run(
                place_order(amount, direction, market_index, sub_account_id)
            )

            return f"Order placed successfully. Transaction signature: {tx_sig}"

        except json.JSONDecodeError:
            return "Error: Input must be a valid JSON string"
        except Exception as e:
            print(e)
            return f"Error placing order: {str(e)}"

    async def _arun(self, amount: float, direction: str, symbol: str) -> str:
        """Async version of _run"""
        try:
            market_index = drift_perp_markets_dict[symbol]["marketIndex"]
            sub_account_id = 0

            if not amount:
                return "Error: Amount is required"

            direction = (
                PositionDirection.Long()
                if direction.lower() == "long"
                else PositionDirection.Short()
            )

            await init()
            tx_sig = await place_order(amount, direction, market_index, sub_account_id)
            await shutdown()

            return f"Order placed successfully. Transaction signature: {tx_sig}"

        except json.JSONDecodeError:
            return "Error: Input must be a valid JSON string"
        except Exception as e:
            print(e)
            return f"Error placing order: {str(e)}"


# Example usage:
async def main():
    order_tool = DriftOrderTool()

    # Example order input
    input_dict = {"amount": 0.1, "direction": "long", "symbol": "SOL"}

    result = await order_tool.arun(input_dict)
    print(result)


if __name__ == "__main__":
    pass
    # asyncio.run(main())
