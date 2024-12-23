from typing import Dict, Optional, Union
import pandas as pd
from datetime import datetime
import importlib.util
import sys
strategy_code = """
def test():
    print("Hello World")
"""


try:
    # Create a temporary module
    spec = importlib.util.spec_from_loader("strategy_module", loader=None)
    module = importlib.util.module_from_spec(spec)
    sys.modules["strategy_module"] = module

    # Execute the strategy code in the module's context
    exec(strategy_code, module.__dict__)

    # Return the strategy function
    module.strategy
except Exception as e:
    raise ValueError(f"Error loading strategy: {str(e)}")
