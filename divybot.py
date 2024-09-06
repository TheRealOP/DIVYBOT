import yfinance as yf
import pandas as pd

from ticker import tickers


def get_financial_value(dataframe, key, fallback_key=None):
    try:
        return dataframe.loc[key].iloc[0]
    except KeyError:
        if fallback_key:
            try:
                return dataframe.loc[fallback_key].iloc[0]
            except KeyError:
                return 0  # Return 0 if both keys are missing
        return 0  # Return 0 if the primary key is missing


def calculate_dividend_growth(ticker, end_date=pd.Timestamp.now()):
    # Fetch dividend history
    stock = yf.Ticker(ticker)
    dividends = stock.dividends

    # Ensure the end_date is in datetime format
    end_date = pd.to_datetime(end_date)

    # Remove timezone information from end_date and convert dividends index to timezone-naive
    end_date = end_date.tz_localize(None)
    dividends.index = dividends.index.tz_localize(None)

    # Calculate the start dates for the past year and the year before
    start_date_last_year = end_date - pd.DateOffset(years=1)
    start_date_year_before = start_date_last_year - pd.DateOffset(years=1)

    # Filter dividends for the past year and the year before
    dividends_last_year = dividends.loc[start_date_last_year:end_date]
    dividends_year_before = dividends.loc[start_date_year_before:start_date_last_year]

    # Calculate total dividends for each period
    total_dividends_last_year = dividends_last_year.sum()
    total_dividends_year_before = dividends_year_before.sum()

    # Calculate dividend growth rate
    if total_dividends_year_before == 0:
        return 0  # Avoid division by zero

    dividend_growth_rate = (total_dividends_last_year - total_dividends_year_before) / total_dividends_year_before

    return dividend_growth_rate * 100


def calculate_fcfe(ticker, end_date=pd.Timestamp.now()):
    # Fetch financial data
    stock = yf.Ticker(ticker)
    financials = stock.financials
    cashflow = stock.cashflow
    balance_sheet = stock.balance_sheet

    # Ensure the end_date is in datetime format
    end_date = pd.to_datetime(end_date)

    # Extract the relevant data
    net_income = get_financial_value(financials, 'Net Income')
    depreciation = get_financial_value(cashflow, 'Depreciation', 'Depreciation & Amortization')
    capex = get_financial_value(cashflow, 'Capital Expenditures')

    # Calculate changes in working capital
    current_assets_end = get_financial_value(balance_sheet, 'Total Current Assets')
    current_assets_start = get_financial_value(balance_sheet, 'Total Current Assets', 'Total Current Assets')
    current_liabilities_end = get_financial_value(balance_sheet, 'Total Current Liabilities')
    current_liabilities_start = get_financial_value(balance_sheet, 'Total Current Liabilities',
                                                    'Total Current Liabilities')

    change_in_working_capital = (current_assets_end - current_liabilities_end) - (
            current_assets_start - current_liabilities_start)

    # Calculate net borrowing
    debt_end = get_financial_value(balance_sheet, 'Long Term Debt')
    debt_start = get_financial_value(balance_sheet, 'Long Term Debt', 'Long Term Debt')
    net_borrowing = debt_end - debt_start

    # Calculate FCFE
    fcfe = net_income + depreciation - capex - change_in_working_capital + net_borrowing

    return fcfe


def calculate_200_sma_comparison(ticker, end_date=pd.Timestamp.now()):
    # Fetch historical price data
    stock = yf.Ticker(ticker)
    history = stock.history(period='1y')  # Fetch 1 year of data to ensure we have enough for 200 SMA

    # Ensure the end_date is in datetime format and remove timezone information
    end_date = pd.to_datetime(end_date).tz_localize(None)
    history.index = history.index.tz_localize(None)

    # Filter the data up to the end_date
    history = history.loc[:end_date]

    # Ensure there is enough data to calculate the 200-day SMA
    if len(history) < 200:
        return 0  # Not enough data to calculate 200-day SMA

    # Calculate the 200-day SMA
    history['200_SMA'] = history['Close'].rolling(window=200).mean()

    # Get the current price and the most recent 200-day SMA value
    current_price = history['Close'].iloc[-1]
    sma_200 = history['200_SMA'].iloc[-1]

    # Calculate the percentage difference
    sma_comparison = (current_price - sma_200) / sma_200 if sma_200 != 0 else 0

    return sma_comparison


def calculate_dividend_yield(ticker):
    # Fetch historical price and dividend data
    stock = yf.Ticker(ticker)
    history = stock.history(period='1y')
    dividends = stock.dividends

    # Ensure there's at least one dividend payment
    if dividends.empty:
        return 0

    # Calculate the annual dividend (sum of the last year dividends)
    annual_dividend = dividends[-4:].sum()  # Assuming quarterly dividends

    # Get the current stock price
    current_price = history['Close'].iloc[-1]

    # Calculate dividend yield
    dividend_yield = annual_dividend / current_price if current_price != 0 else 0

    return dividend_yield


def normalize(values):
    min_value = min(values)
    max_value = max(values)
    normalized_values = [(value - min_value) / (max_value - min_value) if max_value != min_value else 0 for value in
                         values]
    return normalized_values


def get_distributions(n=5, end_date=pd.Timestamp.now()):
    """
    This function returns the percent of the current cash that you should distribute into the top n number of stocks
    :param end_date: end date...
    :param n: the number of stocks that you want to invest in
    :return:
    """
    weights = [3, 3, 3, 1]

    # calculate dividend growth
    dividend_growth = []
    for ticker in tickers:
        dividend_growth.append(calculate_dividend_growth(ticker, end_date))
    normalized_dividend_growth = normalize(dividend_growth)

    # calculate FCFE
    fcfe = []
    for ticker in tickers:
        fcfe.append(calculate_fcfe(ticker, end_date))
    normalized_fcfe = normalize(fcfe)

    # calculate dip (200 day SMA)
    dip = []
    for ticker in tickers:
        dip.append(calculate_200_sma_comparison(ticker, end_date))
    normalized_dip = normalize(dip)

    # calculate dividend yield
    dividend_yield = []
    for ticker in tickers:
        dividend_yield.append(calculate_dividend_yield(ticker))
    normalized_dividend_yield = normalize(dividend_yield)

    sorted_stonks = []
    for i in range(len(tickers)):
        normalized_dividend_growth[i] *= weights[0]
        normalized_fcfe[i] *= weights[1]
        normalized_dip[i] *= weights[2]
        dividend_yield *= weights[3]
        spam = normalized_dividend_growth[i] + normalized_fcfe[i] + normalized_dip[i] + normalized_dividend_yield[i]
        sorted_stonks.append((tickers[i], spam))

    sorted_stonks.sort(key=lambda item: item[1], reverse=True)
    sum = 0
    for thing in sorted_stonks[:n]:
        sum += thing[1]

    distributions = []
    for thing in sorted_stonks[:n]:
        distributions.append((thing[0], round(100 * thing[1] / sum)))

    return distributions


'''
def backtest(start_date, end_date, initial_cash=10000, n=5):
    # Get the initial distributions
    distributions = get_distributions(n, end_date=start_date)

    # Initialize the portfolio
    portfolio = {ticker: 0 for ticker, _ in distributions}
    cash = initial_cash

    # Fetch historical data for all tickers in the portfolio
    tickers = [ticker for ticker, _ in distributions]
    data = yf.download(tickers, start=start_date, end=end_date)['Adj Close']

    # Invest initial cash based on distributions
    for ticker, percent in distributions:
        investment = (percent / 100) * initial_cash
        portfolio[ticker] = investment / data[ticker].iloc[0]

    # Calculate portfolio value over time
    portfolio_values = []
    dates = data.index
    for date in dates:
        value = sum(data[ticker].loc[date] * portfolio[ticker] for ticker in portfolio) + cash
        portfolio_values.append(value)

    # Convert to DataFrame
    portfolio_df = pd.DataFrame({'Date': dates, 'Portfolio Value': portfolio_values})
    portfolio_df.set_index('Date', inplace=True)

    # Calculate performance metrics
    total_return = (portfolio_values[-1] - initial_cash) / initial_cash
    annualized_return = ((1 + total_return) ** (365 / (dates[-1] - dates[0]).days)) - 1
    daily_returns = portfolio_df['Portfolio Value'].pct_change().dropna()
    volatility = daily_returns.std() * np.sqrt(252)

    return portfolio_df, total_return, annualized_return, volatility


# Example usage
start_date = '2020-01-01'
end_date = '2024-06-01'
portfolio_df, total_return, annualized_return, volatility = backtest(start_date, end_date)

print(f"Total Return: {total_return * 100:.2f}%")
print(f"Annualized Return: {annualized_return * 100:.2f}%")
print(f"Volatility: {volatility * 100:.2f}%")
portfolio_df.plot(title='Portfolio Value Over Time')
plt.show()
'''
