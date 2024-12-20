import asyncio
from solana.rpc.async_api import AsyncClient
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def main():
    # Alternatively, close the client explicitly instead of using a context manager:
    client = AsyncClient("https://api.mainnet-beta.solana.com", timeout=100000)
    res = await client.is_connected()
    logging.info("test")
    logging.info(res)  # True
    await client.close()

asyncio.run(main())
