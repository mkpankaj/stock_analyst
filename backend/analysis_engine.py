import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import AnalysisResult, StockPrice
import numpy as np

def get_price_at_day(prices_df: pd.DataFrame, day_num: int) -> float:
    if prices_df is None or prices_df.empty:
        return None
    if day_num < 0 or day_num >= len(prices_df):
        return None
    return prices_df.iloc[day_num]['close']

def calculate_trend(prices_df: pd.DataFrame) -> str:
    if prices_df is None or prices_df.empty or len(prices_df) < 30:
        return "Unknown"

    price_d1 = prices_df.iloc[0]['close']
    price_d120 = prices_df.iloc[-1]['close']

    if len(prices_df) < 30:
        return "Insufficient Data"

    price_d90 = prices_df.iloc[-30]['close'] if len(prices_df) > 30 else prices_df.iloc[0]['close']

    overall_change = (price_d120 - price_d1) / price_d1
    last_30_change = (price_d120 - price_d90) / price_d90

    is_uptrend = overall_change > 0
    strong_last_30 = last_30_change > 0

    if is_uptrend and strong_last_30:
        return "Strong Upward"
    elif is_uptrend and abs(last_30_change) < 0.04:
        return "Weak Uptrend"
    elif not is_uptrend and last_30_change < 0:
        return "Strong Downward"
    elif not is_uptrend and abs(last_30_change) < 0.04:
        return "Weak Downtrend"
    else:
        return "Neutral"

def get_weekly_prices(prices_df: pd.DataFrame) -> pd.DataFrame:
    if prices_df is None or prices_df.empty:
        return None

    prices_df['date'] = pd.to_datetime(prices_df['date'])
    prices_df['week'] = prices_df['date'].dt.isocalendar().week
    prices_df['year'] = prices_df['date'].dt.isocalendar().year

    weekly = prices_df.groupby(['year', 'week'])['close'].agg(['median', 'first', 'last']).reset_index()
    weekly['date'] = prices_df.groupby(['year', 'week'])['date'].last().values

    return weekly

def analyze_stocks(db: Session, tickers: list, duration_days: int) -> dict:
    analysis_results = {'gainers': [], 'losers': [], 'errors': []}
    stock_metrics = []

    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=duration_days)

    for ticker in tickers:
        try:
            prices = db.query(StockPrice).filter(
                StockPrice.ticker == ticker,
                StockPrice.date >= start_date,
                StockPrice.date <= end_date
            ).order_by(StockPrice.date).all()

            if not prices:
                continue

            prices_df = pd.DataFrame({
                'date': [p.date for p in prices],
                'open': [p.open for p in prices],
                'high': [p.high for p in prices],
                'low': [p.low for p in prices],
                'close': [p.close for p in prices]
            })

            coverage = len(prices_df) / duration_days
            if coverage < 0.8:
                continue

            price_d1 = prices_df.iloc[0]['close']
            price_d120 = prices_df.iloc[-1]['close']
            price_change_pct = ((price_d120 - price_d1) / price_d1) * 100

            trend = calculate_trend(prices_df)

            stock_metrics.append({
                'ticker': ticker,
                'price_change_pct': price_change_pct,
                'trend': trend,
                'price_d1': price_d1,
                'price_d120': price_d120
            })
        except Exception as e:
            analysis_results['errors'].append({'ticker': ticker, 'error': str(e)})

    if not stock_metrics:
        return analysis_results

    metrics_df = pd.DataFrame(stock_metrics)
    metrics_df_sorted_asc = metrics_df.sort_values('price_change_pct', ascending=True)
    metrics_df_sorted_desc = metrics_df.sort_values('price_change_pct', ascending=False)

    for idx, row in metrics_df_sorted_desc.head(10).iterrows():
        analysis_results['gainers'].append({
            'rank': len(analysis_results['gainers']) + 1,
            'ticker': row['ticker'],
            'price_change_pct': round(row['price_change_pct'], 2),
            'trend': row['trend'],
            'price_d1': round(row['price_d1'], 2),
            'price_d120': round(row['price_d120'], 2)
        })

    for idx, row in metrics_df_sorted_asc.head(10).iterrows():
        analysis_results['losers'].append({
            'rank': len(analysis_results['losers']) + 1,
            'ticker': row['ticker'],
            'price_change_pct': round(row['price_change_pct'], 2),
            'trend': row['trend'],
            'price_d1': round(row['price_d1'], 2),
            'price_d120': round(row['price_d120'], 2)
        })

    return analysis_results
