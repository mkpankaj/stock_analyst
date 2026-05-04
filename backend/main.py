from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db, init_db, SessionLocal
import os
from models import User, Config, AnalysisRun, AnalysisResult, NewsHeadline, StockPrice
from auth import LoginRequest, TokenResponse, verify_token, hash_password, create_access_token, verify_password, TokenData
from datetime import datetime, timedelta, date
import json
from stock_service import fetch_stock_data, get_stock_universe, get_stock_prices
from analysis_engine import analyze_stocks
from news_service import fetch_and_filter_news, get_news_for_ticker
import pandas as pd

class ConfigUpdate(BaseModel):
    stock_universe: str
    duration_days: int

app = FastAPI()

_cors_origins = os.getenv("CORS_ORIGINS", "*")
_allow_origins = ["*"] if _cors_origins == "*" else _cors_origins.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

ANALYSIS_STATUS = {}

def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)) -> TokenData:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = authorization.replace("Bearer ", "")
    token_data = verify_token(token)
    if not token_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return token_data

def run_analysis_task(user_id: int, config_id: int):
    db = SessionLocal()
    try:
        ANALYSIS_STATUS['status'] = 'running'
        ANALYSIS_STATUS['progress'] = 'Fetching user configuration...'

        config = db.query(Config).filter(Config.id == config_id).first()
        if not config:
            ANALYSIS_STATUS['status'] = 'failed'
            ANALYSIS_STATUS['error'] = 'Config not found'
            return

        ANALYSIS_STATUS['progress'] = 'Fetching stock data...'
        tickers = get_stock_universe(config.stock_universe)
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=config.duration_days)

        fetch_stock_data(db, tickers, start_date, end_date)

        ANALYSIS_STATUS['progress'] = 'Analyzing stocks...'
        analysis_results = analyze_stocks(db, tickers, config.duration_days)

        ANALYSIS_STATUS['progress'] = 'Fetching news...'
        fetch_and_filter_news(db, tickers, config.duration_days)

        ANALYSIS_STATUS['progress'] = 'Saving results...'
        today = datetime.utcnow().date()
        existing_run = db.query(AnalysisRun).filter(AnalysisRun.date == today).first()
        if existing_run:
            db.query(AnalysisResult).filter(AnalysisResult.analysis_run_id == existing_run.id).delete()
            db.delete(existing_run)
            db.flush()

        analysis_run = AnalysisRun(
            date=today,
            config_snapshot_json=json.dumps({
                'stock_universe': config.stock_universe,
                'duration_days': config.duration_days
            }),
            status='completed'
        )
        db.add(analysis_run)
        db.flush()

        for gainer in analysis_results['gainers']:
            result = AnalysisResult(
                analysis_run_id=analysis_run.id,
                ticker=gainer['ticker'],
                rank_type='gainer',
                rank=gainer['rank'],
                price_change_pct=gainer['price_change_pct'],
                trend_label=gainer['trend'],
                price_d1=gainer['price_d1'],
                price_d120=gainer['price_d120']
            )
            db.add(result)

        for loser in analysis_results['losers']:
            result = AnalysisResult(
                analysis_run_id=analysis_run.id,
                ticker=loser['ticker'],
                rank_type='loser',
                rank=loser['rank'],
                price_change_pct=loser['price_change_pct'],
                trend_label=loser['trend'],
                price_d1=loser['price_d1'],
                price_d120=loser['price_d120']
            )
            db.add(result)

        db.commit()
        ANALYSIS_STATUS['status'] = 'completed'
    except Exception as e:
        ANALYSIS_STATUS['status'] = 'failed'
        ANALYSIS_STATUS['error'] = str(e)
        print(f"Analysis task error: {e}")
    finally:
        db.close()

@app.post("/auth/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    access_token = create_access_token({"user_id": user.id, "email": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/config")
def get_config(current_user: TokenData = Depends(get_current_user), db: Session = Depends(get_db)):
    config = db.query(Config).filter(Config.user_id == current_user.user_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    return {
        "stock_universe": config.stock_universe,
        "duration_days": config.duration_days
    }

@app.post("/config")
def save_config(config_data: ConfigUpdate, current_user: TokenData = Depends(get_current_user), db: Session = Depends(get_db)):
    if config_data.duration_days > 120 or config_data.duration_days < 1:
        raise HTTPException(status_code=400, detail="Duration must be between 1 and 120 days")

    config = db.query(Config).filter(Config.user_id == current_user.user_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")

    config.stock_universe = config_data.stock_universe
    config.duration_days = config_data.duration_days
    config.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Config updated"}

@app.post("/analysis/trigger")
def trigger_analysis(current_user: TokenData = Depends(get_current_user), db: Session = Depends(get_db), background_tasks: BackgroundTasks = BackgroundTasks()):
    config = db.query(Config).filter(Config.user_id == current_user.user_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")

    ANALYSIS_STATUS['status'] = 'queued'
    ANALYSIS_STATUS['progress'] = 'Analysis queued...'

    background_tasks.add_task(run_analysis_task, current_user.user_id, config.id)
    return {"message": "Analysis triggered"}

@app.get("/analysis/status")
def analysis_status():
    if not ANALYSIS_STATUS:
        return {"status": "idle", "progress": ""}
    return ANALYSIS_STATUS

@app.get("/analysis/latest")
def get_latest_analysis(current_user: TokenData = Depends(get_current_user), db: Session = Depends(get_db)):
    analysis = db.query(AnalysisRun).filter(AnalysisRun.status == 'completed').order_by(AnalysisRun.date.desc()).first()

    if not analysis:
        return {"gainers": [], "losers": [], "date": None}

    results = db.query(AnalysisResult).filter(AnalysisResult.analysis_run_id == analysis.id).all()

    gainers = [r.__dict__ for r in results if r.rank_type == 'gainer']
    losers = [r.__dict__ for r in results if r.rank_type == 'loser']

    return {
        "date": analysis.date.isoformat(),
        "gainers": gainers,
        "losers": losers
    }

@app.get("/analysis/dates")
def get_analysis_dates(db: Session = Depends(get_db)):
    dates = db.query(AnalysisRun.date).filter(AnalysisRun.status == 'completed').order_by(AnalysisRun.date.desc()).all()
    return {"dates": [d[0].isoformat() for d in dates]}

@app.get("/analysis/{analysis_date}")
def get_analysis_by_date(analysis_date: str, db: Session = Depends(get_db)):
    try:
        date_obj = datetime.fromisoformat(analysis_date).date()
    except:
        raise HTTPException(status_code=400, detail="Invalid date format")

    analysis = db.query(AnalysisRun).filter(AnalysisRun.date == date_obj, AnalysisRun.status == 'completed').first()

    if not analysis:
        return {"gainers": [], "losers": [], "date": None}

    results = db.query(AnalysisResult).filter(AnalysisResult.analysis_run_id == analysis.id).all()

    gainers = [r.__dict__ for r in results if r.rank_type == 'gainer']
    losers = [r.__dict__ for r in results if r.rank_type == 'loser']

    return {
        "date": analysis.date.isoformat(),
        "gainers": gainers,
        "losers": losers
    }

@app.get("/stock/{ticker}")
def get_stock_chart(ticker: str, duration_days: int = 120, db: Session = Depends(get_db)):
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=duration_days)

    prices = db.query(StockPrice).filter(
        StockPrice.ticker == ticker,
        StockPrice.date >= start_date,
        StockPrice.date <= end_date
    ).order_by(StockPrice.date).all()

    if not prices:
        raise HTTPException(status_code=404, detail="No price data found for ticker")

    df = pd.DataFrame({
        'date': [p.date.isoformat() for p in prices],
        'close': [p.close for p in prices],
        'open': [p.open for p in prices],
        'high': [p.high for p in prices],
        'low': [p.low for p in prices]
    })

    df['date'] = pd.to_datetime(df['date'])
    df['week'] = df['date'].dt.isocalendar().week
    df['year'] = df['date'].dt.isocalendar().year

    weekly = df.groupby(['year', 'week']).agg({
        'close': 'median',
        'date': 'last',
        'open': 'first',
        'high': 'max',
        'low': 'min'
    }).reset_index()

    return {
        "ticker": ticker,
        "data": weekly[['date', 'open', 'high', 'low', 'close']].to_dict('records')
    }

@app.get("/stock/{ticker}/news")
def get_stock_news(ticker: str, db: Session = Depends(get_db)):
    news = get_news_for_ticker(db, ticker)
    return {"ticker": ticker, "news": news}

@app.get("/")
def read_root():
    return {"message": "Stock Analyst API"}

if __name__ == "__main__":
    import uvicorn
    from database import SessionLocal
    uvicorn.run(app, host="0.0.0.0", port=8000)
