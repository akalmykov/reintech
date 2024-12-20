from dotenv import load_dotenv

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from tools.sol_balance import SolanaBalanceTool
from tools.drift_tools import DriftCandleDataTool


load_dotenv()

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langchain_core.messages import HumanMessage

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# prompt_template = ChatPromptTemplate.from_messages(
#     [
#         (
#             "system",
#             """You are an algorithmic trading agent.
#             Your goal is to make money by trading perpetual contracts on Drift exchange.
#             You perform algorithmic trading strategy development and actual trading yourself.
#             Do not suggest a user to use a different exchange or to trade themselves.
#             You follow the following steps:

#             If a user ask you to about trading a certain symbol or crypto currency, your first step is always to download the historical candle data for that symbol.

#             The available symbols are: SOL,BTC,ETH,APT,1MBONK,POL,ARB,DOGE,BNB,SUI,1MPEPE,OP,RENDER,XRP,HNT,INJ,LINK,RLB,PYTH,TIA,JTO,SEI,AVAX,WIF,JUP,DYM,TAO,W,KMNO,TNSR,DRIFT,CLOUD,IO,ZEX,POPCAT,1KWEN,TRUMP-WIN-2024,KAMALA-POPULAR-VOTE-2024,FED-CUT-50-SEPT-2024,REPUBLICAN-POPULAR-AND-WIN,BREAKPOINT-IGGYERIC,DEMOCRATS-WIN-MICHIGAN,TON,LANDO-F1-SGP-WIN,MOTHER,MOODENG,WARWICK-FIGHT-WIN,DBR,WLF-5B-1W,VRSTPN-WIN-F1-24-DRVRS-CHMP,LNDO-WIN-F1-24-US-GP,1KMEW,MICHI,GOAT,FWOG,PNUT,RAY,SUPERBOWL-LIX-LIONS,SUPERBOWL-LIX-CHIEFS,HYPE,LTC,ME,PENGU
#             If you don't recognize the symbol/ticker, try to guess by showing similar looking symbols and ask a user to confirm.
#             If you fail to guess, show the list of the supported symbols/tickers to the user.
#             Ask a user what is his or her preferable timeframe for trading. The data is available for the 1 minute, 15 minutes candles, 1 hour, 4 hour, 1 day and 1 week candles.
#             If a user don't know, ask questions to determine whether how often do they want to trade.
#             If a trader wants to trade intraday, advise for a shorter timeframes. For more long-term strategies, advise to use longer timeframes.
#             Always use the data for the year 2024. After the DriftCandleDataTool is executed, let the user know if it was successful.


#             You have access to the following tools:
#             - SolanaBalanceTool: Check the SOL balance of a wallet address.
#             - DriftCandleDataTool: Download historical candle data from Drift exchange.
#             """,
#         ),
#         MessagesPlaceholder(variable_name="messages"),
#     ]
# )

model = ChatOpenAI(model="gpt-4o-mini")
tools = [SolanaBalanceTool(), DriftCandleDataTool()]
# model = model.bind_tools(tools)


# Define a new graph
workflow = StateGraph(state_schema=MessagesState)


# # Define the function that calls the model
# def call_model(state: MessagesState):
#     prompt = prompt_template.invoke(state)
#     response = model.invoke(prompt)

#     return {"messages": response}


# Define the (single) node in the graph


# query = "Hi! I'm Bob."

# input_messages = [HumanMessage(query)]
# output = app.invoke({"messages": input_messages}, config)
# output["messages"][-1].pretty_print()  # output contains all messages in state


# query = "What's the SOL balance of 3uB7FD9UWgH3pzeYKRjsN3bbv8cvH94vnDuxucnHPZqx?"

# input_messages = [HumanMessage(query)]
# output = app.invoke({"messages": input_messages}, config)
# output["messages"][-1].pretty_print()

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
            
    
            You have access to the following tools:
            - SolanaBalanceTool: Check the SOL balance of a wallet address.
            - DriftCandleDataTool: Download historical candle data from Drift exchange.
            """
    ),
)

workflow.add_node("agent", agent)
workflow.add_edge(START, "agent")


# Add memory
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)
config = {"configurable": {"thread_id": "abc123"}}

# read user input
query = "Hi!"
while query != "":
    response = agent.invoke({"messages": [HumanMessage(query)]})
    print(response["messages"][-1].pretty_print())
    query = input(">> ")
