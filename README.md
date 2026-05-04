# Stock Analyst - MVP Web Application

A lightweight web application for analyzing Indian stock market data (NIFTY 50/100). The app fetches stock prices from Yahoo Finance, identifies top gainers/losers, analyzes trends, and surfaces relevant news from RSS feeds.

## Quick Start

### 1. Backend Setup

```bash
cd backend
pip install -r requirements.txt
python seed_users.py  # Create test users
python main.py        # Start FastAPI server (runs on http://localhost:8000)
```

**Test Users:**
- user1@test.com / password1
- user2@test.com / password2
- user3@test.com / password3

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev  # Start dev server (runs on http://localhost:5173)
```

### 3. Access the Application

Open http://localhost:5173 in your browser.

---

## Features

### Authentication
- Simple login with email and password (no registration needed for MVP)
- JWT token-based authentication
- Pre-seeded test users for quick testing

### Home Page
- View latest stock analysis (Top 10 Gainers & Losers)
- Manually trigger stock analysis (max 2 per day)
- Load previous analyses by date
- Click any stock to view detailed chart and news

### Configuration Page
- Select stock universe: NIFTY 50 or NIFTY 100
- Set analysis duration: 1-120 days
- Default: NIFTY 50 for 120 days

### Stock Detail Page
- Weekly price chart (last 4 months)
- Trend classification (Strong Upward, Weak Uptrend, Strong Downward, Weak Downtrend)
- Latest news headlines from Business Standard, LiveMint, Economic Times

---

## Architecture

### Backend (FastAPI + Python)
- **Database**: SQLite (single file: `stock_analyst.db`)
- **Libraries**: yfinance, feedparser, SQLAlchemy
- **Key Modules**:
  - `stock_service.py`: Incremental stock data fetching
  - `analysis_engine.py`: Gainers/losers and trend analysis
  - `news_service.py`: RSS feed parsing and filtering
  - `models.py`: Database schema
  - `auth.py`: JWT authentication

### Frontend (React + Vite)
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **HTTP Client**: Axios
- **Routing**: React Router v6
- **4 Pages**: Login, Home, Config, Stock Detail

---

## Business Logic

### Stock Data Fetching
- Incremental fetch: Only fetches new data since last run
- Drops stocks with < 80% data coverage for the period
- Daily data stored in database; weekly aggregation for charts

### Analysis Computation
- **Top Gainers/Losers**: Based on price change from Day 1 to Day 120
- **Trend Classification**:
  - Strong Upward: Overall increase + positive slope in last 30 days
  - Weak Uptrend: Overall increase + < 4% change in last 30 days
  - Strong Downward: Overall decrease + negative slope in last 30 days
  - Weak Downtrend: Overall decrease + < 4% change in last 30 days

### News Filtering
- Fetches RSS feeds from 3 major Indian business publications
- Filters headlines by company name (case-insensitive)
- Stores headlines and links in database

### Rate Limiting
- Maximum 2 analysis triggers per user per day
- One analysis per calendar date (overwrites if re-run on same day)

---

## API Endpoints

### Authentication
- `POST /auth/login` - Login and get JWT token
- `GET /auth/trigger-count` - Check remaining triggers for today

### Configuration
- `GET /config` - Get user's analysis configuration
- `POST /config` - Save configuration (stock universe, duration)

### Analysis
- `POST /analysis/trigger` - Trigger a new analysis (background task)
- `GET /analysis/status` - Check analysis progress
- `GET /analysis/latest` - Get latest completed analysis
- `GET /analysis/{date}` - Get analysis for specific date
- `GET /analysis/dates` - List all analysis dates

### Stock Data
- `GET /stock/{ticker}` - Get weekly price chart data
- `GET /stock/{ticker}/news` - Get news headlines for stock

---

## File Structure

```
stock_analyst/
├── backend/
│   ├── main.py                  # FastAPI app with all routes
│   ├── models.py                # SQLAlchemy ORM models
│   ├── database.py              # SQLite setup
│   ├── auth.py                  # JWT authentication
│   ├── stock_service.py         # Stock data fetching
│   ├── analysis_engine.py       # Stock analysis logic
│   ├── news_service.py          # RSS feed parsing
│   ├── seed_users.py            # Create test users
│   ├── requirements.txt
│   ├── .env                     # JWT_SECRET (create before running)
│   └── stock_analyst.db         # SQLite database (auto-created)
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── LoginPage.jsx
│   │   │   ├── HomePage.jsx
│   │   │   ├── ConfigPage.jsx
│   │   │   └── StockPage.jsx
│   │   ├── api.js               # Axios API client
│   │   ├── App.jsx              # React Router setup
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── postcss.config.js
└── README.md
```

---

## Technology Stack Summary

| Layer | Technology |
|-------|-----------|
| Frontend | React + Vite + Tailwind CSS + Recharts |
| Backend | FastAPI + Python |
| Database | SQLite |
| Stock Data | Yahoo Finance (yfinance) |
| News | RSS Feeds (feedparser) |
| Auth | JWT |
| HTTP Client | Axios |

---

## Development Notes

### Adding More Stocks
Edit `NIFTY_50` list in `backend/stock_service.py` and `COMPANY_NAMES` mapping in `backend/news_service.py`.

### Changing News Sources
Update `RSS_FEEDS` dict in `backend/news_service.py` with new feed URLs.

### Running Tests
Backend provides a detailed status API at `GET /analysis/status` to monitor analysis progress.

### Database Reset
Delete `backend/stock_analyst.db` and run `seed_users.py` again to reset the database.

---

## Deployment (Future)

For future deployment to cloud:
1. Create a production `.env` file with a strong `JWT_SECRET`
2. Use a proper database (PostgreSQL) instead of SQLite
3. Deploy backend to services like Railway, Render, or AWS
4. Deploy frontend to Vercel or Netlify
5. Update `API_BASE_URL` in frontend `api.js` to production backend URL

---

## Known Limitations (MVP)

1. No user registration - uses pre-seeded accounts only
2. Limited to NIFTY 50/100 (can be easily extended)
3. Manual trigger only - no scheduled automated analysis
4. Local SQLite database - not suitable for multiple concurrent users
5. Simple password hashing (SHA256) - use bcrypt for production
6. No email verification or password reset
7. Analysis runs sequentially on demand - no background queue system

---

## Next Steps for Production

1. Add user registration and email verification
2. Implement role-based access control
3. Add data export capabilities (CSV, PDF)
4. Set up automated scheduled analysis
5. Add more technical indicators and analysis metrics
6. Implement real-time stock price updates
7. Add portfolio tracking and alerts
8. Set up comprehensive error logging and monitoring

---

## License

MIT
