from dotenv import load_dotenv

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from tools.sol_balance import SolanaBalanceTool
from tools.drift_tools import DriftCandleDataTool
from tools.backtesting_tool import BacktestingTool


load_dotenv()

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langchain_core.messages import HumanMessage

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


model = ChatOpenAI(model="gpt-4o-mini")
tools = [SolanaBalanceTool(), DriftCandleDataTool(), BacktestingTool()]
# model = model.bind_tools(tools)


# Define a new graph
workflow = StateGraph(state_schema=MessagesState)


from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage

agent = create_react_agent(
    model=model,
    tools=tools,
    state_modifier=SystemMessage(
        content="""You are an algorithmic trading agent.
            Your goal is to make money by trading perpetual contracts on Drift exchange.
            You perform algorithmic trading strategy development and actual trading yourself. 
            Do not suggest a user to use a different exchange or to trade themselves. 
            You follow the following steps: 
            
            If a user ask you to about trading a certain symbol or crypto currency, your first step is always to download the historical candle data for that symbol. 
            
            The available symbols are: SOL,BTC,ETH,APT,1MBONK,POL,ARB,DOGE,BNB,SUI,1MPEPE,OP,RENDER,XRP,HNT,INJ,LINK,RLB,PYTH,TIA,JTO,SEI,AVAX,WIF,JUP,DYM,TAO,W,KMNO,TNSR,DRIFT,CLOUD,IO,ZEX,POPCAT,1KWEN,TRUMP-WIN-2024,KAMALA-POPULAR-VOTE-2024,FED-CUT-50-SEPT-2024,REPUBLICAN-POPULAR-AND-WIN,BREAKPOINT-IGGYERIC,DEMOCRATS-WIN-MICHIGAN,TON,LANDO-F1-SGP-WIN,MOTHER,MOODENG,WARWICK-FIGHT-WIN,DBR,WLF-5B-1W,VRSTPN-WIN-F1-24-DRVRS-CHMP,LNDO-WIN-F1-24-US-GP,1KMEW,MICHI,GOAT,FWOG,PNUT,RAY,SUPERBOWL-LIX-LIONS,SUPERBOWL-LIX-CHIEFS,HYPE,LTC,ME,PENGU
            If you don't recognize the symbol/ticker, try to guess by showing similar looking symbols and ask a user to confirm.
            If you fail to guess, show the list of the supported symbols/tickers to the user.
            Ask a user what is his or her preferable timeframe for trading. The data is available for the 1 minute, 15 minutes candles, 1 hour, 4 hour, 1 day and 1 week candles.
            If a user don't know, ask questions to determine whether how often do they want to trade. 
            If a trader wants to trade intraday, advise for a shorter timeframes. For more long-term strategies, advise to use longer timeframes.
            Always use the data for the year 2024. After the DriftCandleDataTool is executed, let the user know if it was successful.
            Next, ask a user what is his or her preferable strategy for trading.
            Implement the strategy in Python as the function with following definition:
```            
from typing import Dict, Optional, Union
import pandas as pd
from datetime import datetime

def strategy(
    window_data: pd.DataFrame,
    positions: pd.DataFrame
) -> Optional[Dict[str, Union[int, float, datetime]]]:
    \"""
    Example trading strategy using moving average crossover
    
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
```
            
For example here is the implementation of the Golden/Death cross:

```
from typing import Dict, Optional, Union
import pandas as pd
from datetime import datetime

def golden_cross_death_cross_strategy(
    window_data: pd.DataFrame,
    positions: pd.DataFrame
) -> Optional[Dict[str, Union[int, float, datetime]]]:
    \"""
    Example trading strategy using moving average crossover
    
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
```
            Don't change the function name. Make sure that all Python imports are preserved.
    
            You have access to the following tools:
            - SolanaBalanceTool: Check the SOL balance of a wallet address.
            - DriftCandleDataTool: Download historical candle data from Drift exchange.
            - BacktestingTool: Backtesting on a strategy on historical data.
            """
    ),
)

workflow.add_node("agent1", agent)
workflow.add_edge(START, "agent1")

# Add memory
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)
config = {"configurable": {"thread_id": "abc123"}}

# read user input
query = "Hi!"
while query != "":
    response = app.invoke({"messages": [HumanMessage(query)]}, config)
    print(response["messages"][-1].pretty_print())
    query = input(">> ")


# Cumulative Return
# Annualized Return
# Sharpe Ratio
# Sortino Ratio
# Win Rate
# Maximum Drawdown
# Volatility
# Number of Trades
# Holding Period
