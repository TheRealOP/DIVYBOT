import yfinance as yf
import pandas as pd
import numpy as np
import warnings

from ticker import tickers

# Suppress future warnings
warnings.simplefilter(action='ignore', category=FutureWarning)


# Define a function to fetch stock data and calculate dividend metrics
def get_dividend_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5y")
        dividends = hist['Dividends']

        if dividends.empty:
            return None

        # Remove zeros and NaNs from dividends
        dividends = dividends.replace(0, np.nan).dropna()

        if len(dividends) < 8:
            return None  # Not enough data for growth rate calculation

        # Calculate dividend yield
        current_price = hist['Close'][-1]
        annual_dividend = dividends[-4:].sum()  # Assuming quarterly dividends
        dividend_yield = annual_dividend / current_price

        # Calculate dividend growth rate
        div_growth_rate = (dividends[-1] / dividends[-8]) ** (1 / 2) - 1  # 2-year CAGR

        return {
            'ticker': ticker,
            'dividend_yield': dividend_yield,
            'div_growth_rate': div_growth_rate,
        }
    except Exception as e:
        print(f"Error processing {ticker}: {e}")
        return None



# Fetch data for all tickers and filter for dividend-paying stocks
dividend_data = []
for ticker in tickers:
    data = get_dividend_data(ticker)
    if data:
        dividend_data.append(data)

# Convert to DataFrame
df = pd.DataFrame(dividend_data)


# Rank stocks based on dividend yield and growth rate
df['rank'] = df['dividend_yield'] * df['div_growth_rate']
df = df.sort_values(by='rank', ascending=False)

# Display the top stocks
print(df[['ticker', 'dividend_yield', 'div_growth_rate']])

# Save to JSON
df.to_json('dividend_stocks.json', orient='records')
