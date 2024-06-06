# Basic Setup

# Imports
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

from api_keys import api_key , secret_key;
# Set up the trading client
client = TradingClient(api_key, secret_key, paper=True)


# Returns a Market Order Object
# Does not actually buy/sell anything
# Time in force defaults to day
def createMarketOrder(stock_symbol: str, quantity: float, buy: bool):
    return MarketOrderRequest(
        symbol=stock_symbol,
        qty=quantity,
        side=OrderSide.BUY if buy else OrderSide.SELL,
        time_in_force=TimeInForce.DAY)


# Submits the request to buy/sell stock from ^
# Returns data
def submitMarketOrder(marketOrder):
    order = client.submit_order(order_data=marketOrder)


# Immediately buy 1 stock of your choice
def buyImmediate(symbol: str):
    submitMarketOrder(createMarketOrder(symbol, 1, True))


# Immediately sell 1 stock of your choice
# Does not work if you do not have the stock
def sellImmediate(symbol: str):
    try:
        submitMarketOrder(createMarketOrder(symbol, 1, False))
    except:
        print('ERROR: ur broke bruh')


