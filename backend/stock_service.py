import yfinance as yf
from sqlalchemy.orm import Session
from models import StockPrice
from datetime import datetime, timedelta
import pandas as pd

NIFTY_50 = [
    'RELIANCE.NS', 'HDFCBANK.NS', 'BHARTIARTL.NS', 'SBIN.NS', 'ICICIBANK.NS','TCS.NS', 
    'BAJFINANCE.NS', 'LT.NS', 'HINDUNILVR.NS', 'INFY.NS', 'SUNPHARMA.NS', 'MARUTI.NS',
    'ADANIPORTS.NS', 'AXISBANK.NS', 'ITC.NS', 'TITAN.NS', 'KOTAKBANK.NS', 'ONGC.NS',
    'ULTRACEMCO.NS', 'ADANIENT.NS', 'HCLTECH.NS', 'BEL.NS', 'JSWSTEEL.NS', 'POWERGRID.NS',
    'COALINDIA.NS', 'BAJAJ-AUTO.NS', 'BAJAJFINSV.NS', 'NESTLEIND.NS',  'TATASTEEL.NS', 
    'ASIANPAINT.NS', 
]
def get_stock_universe(stock_universe_str: str) -> list:
    return NIFTY_50

def get_last_fetch_date(db: Session, ticker: str) -> datetime.date:
    last_price = db.query(StockPrice).filter(StockPrice.ticker == ticker).order_by(StockPrice.date.desc()).first()
    if not last_price:
        return None
    return last_price.date

def fetch_stock_data(db: Session, tickers: list, start_date: datetime.date, end_date: datetime.date = None):
    if end_date is None:
        end_date = datetime.utcnow().date()

    status_msg = "Fetching stock data..."
    results = {}

    for ticker in tickers:
        try:
            last_fetch = get_last_fetch_date(db, ticker)
            if last_fetch and last_fetch >= end_date:
                continue

            fetch_from = last_fetch + timedelta(days=1) if last_fetch else start_date

            data = yf.download(
                ticker,
                start=fetch_from,
                end=end_date,
                progress=False,
                ignore_tz=True
            )

            if data.empty:
                results[ticker] = "No data"
                continue

            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            if isinstance(data.index, pd.DatetimeIndex):
                data = data.dropna(subset=['Open', 'High', 'Low', 'Close'])
                for idx, row in data.iterrows():
                    price_date = idx.date() if hasattr(idx, 'date') else idx
                    existing = db.query(StockPrice).filter(
                        StockPrice.ticker == ticker,
                        StockPrice.date == price_date
                    ).first()
                    if not existing:
                        stock_price = StockPrice(
                            ticker=ticker,
                            date=price_date,
                            open=float(row['Open']),
                            high=float(row['High']),
                            low=float(row['Low']),
                            close=float(row['Close'])
                        )
                        db.add(stock_price)
                results[ticker] = "OK"
            else:
                results[ticker] = "Invalid data format"
        except Exception as e:
            results[ticker] = f"Error: {str(e)}"

    db.commit()
    return results

def get_stock_prices(db: Session, ticker: str, start_date: datetime.date, end_date: datetime.date) -> pd.DataFrame:
    prices = db.query(StockPrice).filter(
        StockPrice.ticker == ticker,
        StockPrice.date >= start_date,
        StockPrice.date <= end_date
    ).order_by(StockPrice.date).all()

    if not prices:
        return None

    data = {
        'date': [p.date for p in prices],
        'open': [p.open for p in prices],
        'high': [p.high for p in prices],
        'low': [p.low for p in prices],
        'close': [p.close for p in prices]
    }
    return pd.DataFrame(data)

def check_data_coverage(prices_df: pd.DataFrame, duration_days: int) -> float:
    if prices_df is None or prices_df.empty:
        return 0.0
    return len(prices_df) / duration_days

def get_price_on_day(prices_df: pd.DataFrame, day_offset: int) -> float:
    if prices_df is None or prices_df.empty or day_offset < 0 or day_offset >= len(prices_df):
        return None
    return prices_df.iloc[day_offset]['close']
