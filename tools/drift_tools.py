from .drift_constants import drift_perp_markets_dict
from typing import Optional, Literal
from langchain_core.tools import BaseTool
import aiohttp
import asyncio
from loguru import logger
import os
from enum import Enum
import pandas as pd
from datetime import datetime


class CandleResolution(Enum):
    ONE_MINUTE = "1"
    FIFTEEN_MINUTES = "15"
    ONE_HOUR = "60"
    FOUR_HOURS = "240"
    ONE_DAY = "D"
    ONE_WEEK = "W"


class DriftCandleDataTool(BaseTool):
    name: str = "drift_candle_data"
    description: str = """
    Downloads historical candle data from Drift exchange.
    Use this tool to download data for the ticker a user is interested in.
    Input should be a JSON string with the following parameters:
    - base_asset_symbol: Base asset symbol (e.g., "SOL")
    - resolution: Candle resolution: "1", "15", "60", "240", "D", "W". 
    "1" is for a 1 minute candle, "15" is for 15 minute candles, "60" is for 1 hour candles, 
    "240" is for 4 hours candles, "D" is for daily candles, "W" is for weekly candles
    - year: Year of data (e.g., "2024")
    Returns the path to the downloaded CSV file. If an error occurs, it will return an error message.
    """

    base_url: str = """
    Base URL for the drift historical data.
    Default is https://drift-historical-data-v2.s3.eu-west-1.amazonaws.com
    """
    program_id: str = """
    Program ID for the drift historical data.
    Default is dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH
    """
    download_dir: str = """
    Directory to download the CSV file.
    Default is data
    """

    def __init__(
        self,
        base_url: str = "https://drift-historical-data-v2.s3.eu-west-1.amazonaws.com",
        program_id: str = "dRiftyHA39MWEi3m9aunc5MzRF1JYuBsbn6VPcn33UH",
        download_dir: str = "data",
    ):
        super().__init__()
        self.base_url = base_url
        self.program_id = program_id
        self.download_dir = download_dir

        # Create download directory if it doesn't exist
        os.makedirs(download_dir, exist_ok=True)

    def _build_url(self, year: str, base_asset_symbol: str, resolution: str) -> str:
        """Build the URL for the candle data"""
        return f"{self.base_url}/program/{self.program_id}/candle-history/{year}/perp_{drift_perp_markets_dict[base_asset_symbol]['marketIndex']}/{resolution}.csv"

    def _get_output_path(
        self, base_asset_symbol: str, resolution: str, year: str
    ) -> str:
        """Generate the output file path"""
        return os.path.join(
            self.download_dir, f"perp_{base_asset_symbol}_{resolution}_{year}.csv"
        )

    async def _download_file(self, url: str, output_path: str) -> None:
        """Download the CSV file"""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    with open(output_path, "wb") as f:
                        while True:
                            chunk = await response.content.read(8192)
                            if not chunk:
                                break
                            f.write(chunk)
                else:
                    raise Exception(f"Failed to download file: HTTP {response.status}")

    async def _arun(self, base_asset_symbol: str, resolution: str, year: str) -> str:
        """Async run the candle data download"""
        try:
            if base_asset_symbol not in drift_perp_markets_dict:
                return f"Error: Invalid base asset symbol. Must be one of {[m['baseAssetSymbol'] for m in drift_perp_markets]}"
            # Validate resolution
            if resolution not in [r.value for r in CandleResolution]:
                return f"Error: Invalid resolution. Must be one of {[r.value for r in CandleResolution]}"

            # Validate year
            current_year = str(datetime.now().year)
            if not year.isdigit() or int(year) > int(current_year):
                return f"Error: Invalid year. Must be a valid year up to {current_year}"

            # Build URL and output path
            url = self._build_url(year, base_asset_symbol, resolution)
            output_path = self._get_output_path(base_asset_symbol, resolution, year)

            # Download file
            await self._download_file(url, output_path)

            # Validate downloaded file
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                # Load and validate CSV
                df = pd.read_csv(output_path)
                row_count = len(df)
                return f"Successfully downloaded historical data for {base_asset_symbol} with resolution {resolution} for year {year} to {output_path}"
            else:
                return f"Error: Downloaded file is empty or invalid"

        except Exception as e:
            logger.error(f"Error downloading candle data: {e}")
            return f"Error: {str(e)}"

    def _run(self, base_asset_symbol: str, resolution: str, year: str) -> str:
        """Synchronous run - wraps async method"""
        return asyncio.run(self._arun(base_asset_symbol, resolution, year))


# Example usage:
async def main():
    # Initialize the tool
    drift_data_tool = DriftCandleDataTool()

    # Example parameters
    base_asset_symbol = "SOL"  # SOL-PERP
    resolution = "D"  # Daily candles
    year = "2024"

    # Download data
    result = await drift_data_tool._arun(
        base_asset_symbol,
        resolution,
        year,
    )
    print(result)


if __name__ == "__main__":
    # Run example
    asyncio.run(main())
