from solana.rpc.api import Client

http_client = Client("https://mainnet.helius-rpc.com/?api-key=4eac2020-576c-4809-8c32-4f2155d6a86a")
print(http_client.is_connected())