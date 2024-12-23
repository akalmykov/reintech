import asyncio
import sys
import logging

from driftpy.drift_client import DriftClient
from solana.rpc.async_api import AsyncClient
import os
from anchorpy import Wallet
from driftpy.keypair import load_keypair
from driftpy.types import *
from driftpy.constants.numeric_constants import BASE_PRECISION, PRICE_PRECISION

logging.basicConfig(
    level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s"
)

url = "https://api.mainnet-beta.solana.com"
connection = AsyncClient(url, timeout=100000)

keypair_file = os.path.expanduser("./keypair.json")
keypair = load_keypair(keypair_file)
wallet = Wallet(keypair)
drift_client = DriftClient(
    connection, wallet, "mainnet", perp_market_indexes=[0], spot_market_indexes=[0]
)


async def init():
    await drift_client.subscribe()


async def shutdown():
    await drift_client.account_subscriber.unsubscribe()
    await drift_client.unsubscribe()
    await drift_client.connection.close()


async def create_subaccount():
    tx_sig = await drift_client.initialize_user(sub_account_id=0, name="toly")
    logging.info(tx_sig)


async def deposit(amount, spot_market_index=0, sub_account_id=0):
    # market indices can be found here:
    # https://github.com/drift-labs/protocol-v2/blob/master/sdk/src/constants/spotMarkets.ts
    # https://github.com/drift-labs/protocol-v2/blob/master/sdk/src/constants/perpMarkets.ts

    drift_client.switch_active_user(sub_account_id=sub_account_id)
    amount = drift_client.convert_to_spot_precision(amount, spot_market_index)  # $100
    logging.info(f"convert_to_spot_precision: {amount} ")
    token_account = drift_client.get_associated_token_account_public_key(
        spot_market_index
    )
    tx_sig = await drift_client.deposit(amount, spot_market_index, token_account)
    logging.info(tx_sig)


async def place_order(
    amount, direction=PositionDirection.Long(), market_index=0, sub_account_id=0
):
    await drift_client.subscribe()
    drift_client.switch_active_user(sub_account_id=sub_account_id)

    order_params = OrderParams(
        order_type=OrderType.Market(),
        base_asset_amount=drift_client.convert_to_perp_precision(amount),
        market_index=market_index,
        direction=direction,
    )
    tx_sig = await drift_client.place_perp_order(order_params)
    logging.info(tx_sig)


async def main(sub_account_id=0):
    drift_client.switch_active_user(sub_account_id=sub_account_id)
    await drift_client.account_subscriber.subscribe()

    user = drift_client.get_user(sub_account_id=0)
    await user.subscribe()

    orders = user.get_open_orders()
    logging.info(orders)
    # order_id = 1;
    # await drift_client.cancel_order(order_id);

    pass


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        # Run the main function
        loop.run_until_complete(init())
        # exit_code = loop.run_until_complete(main())
        exit_code = loop.run_until_complete(place_order(0.1, PositionDirection.Long()))
        loop.run_until_complete(shutdown())
        sys.exit(exit_code or 0)
    except Exception as e:
        logging.error(f"Failed to run main loop: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Cleanup the loop
        loop.close()
