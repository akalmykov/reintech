from typing import Optional
from langchain_core.tools import BaseTool
from solana.rpc.async_api import AsyncClient
import asyncio
from loguru import logger
from solders.pubkey import Pubkey


class SolanaBalanceTool(BaseTool):
    name: str = "solana_balance"
    description: str = """
    Useful for checking SOL balance of a Solana wallet address.
    Input should be a valid Solana public key/wallet address.
    Returns the balance in SOL.
    """
    rpc_url: str = """
    RPC url for the Solana network. 
    Default is mainnet-beta. 
    Do not change this unless specifically asked to use a different network.
    """

    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com"):
        super().__init__()
        self.rpc_url = rpc_url

    async def _arun(self, address: str) -> str:
        """Async run the SOL balance check"""
        try:
            client = AsyncClient(self.rpc_url)

            # Query balance
            response = await client.get_balance(Pubkey.from_string(address))

            balance_lamports = response.value  # Direct access to value
            balance_sol = balance_lamports / 1e9
            return f"Balance: {balance_sol:.9f} SOL"

        except Exception as e:
            logger.error(f"Error querying Solana balance: {e}")
            return f"Error: {str(e)}"
        finally:
            if client:
                pass
                # client.close()

    def _run(self, address: str) -> str:
        """Synchronous run - wraps async method"""
        return asyncio.run(self._arun(address))


# Example usage:
async def main():
    # Initialize the tool
    sol_balance_tool = SolanaBalanceTool()

    # Example address (Replace with actual address)
    address = "DYw8jCTfwHNRJhhmFcbXvVDTqWMEVFBX6ZKUmG5CNSKK"

    # Query balance
    result = await sol_balance_tool._arun(address)
    print(result)


if __name__ == "__main__":
    # Run example
    asyncio.run(main())
