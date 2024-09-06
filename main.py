import divybot

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

from api_keys import api_key, secret_key

client = TradingClient(api_key, secret_key, paper=True)
account = client.get_account()

cash = float(account.cash)
distributions = divybot.get_distributions(n=15)

for stonk in distributions:
    market_order = MarketOrderRequest(
        symbol=stonk[0],
        notional=round(float((stonk[1] * cash) / 100), 2),
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY)
    order = client.submit_order(order_data=market_order)
