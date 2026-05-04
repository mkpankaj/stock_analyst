import feedparser
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import NewsHeadline

RSS_FEEDS = {
    'Business Standard': 'https://www.business-standard.com/rss/markets-106.rss',
    'LiveMint': 'https://www.livemint.com/rss/markets',
    'Economic Times': 'https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms'
}

COMPANY_NAMES = {
    # NIFTY 50
    'RELIANCE': 'Reliance Industries',
    'TCS': 'Tata Consultancy Services',
    'INFOSYS': 'Infosys',
    'HDFC': 'HDFC',
    'ICICIBANK': 'ICICI Bank',
    'SBIN': 'State Bank of India',
    'BAJAJFINSV': 'Bajaj Finserv',
    'LT': 'Larsen & Toubro',
    'HCLTECH': 'HCL Technologies',
    'WIPRO': 'Wipro',
    'MARUTI': 'Maruti Suzuki',
    'SUNPHARMA': 'Sun Pharmaceutical',
    'TECHM': 'Tech Mahindra',
    'INDUSINDBANK': 'IndusInd Bank',
    'ITC': 'ITC',
    'HEROMOTOCO': 'Hero MotoCorp',
    'TITAN': 'Titan',
    'NESTLEIND': 'Nestle India',
    'ASIANPAINT': 'Asian Paints',
    'KOTAKBANK': 'Kotak Mahindra Bank',
    'DMART': 'Avenue Supermarts',
    'AXISBANK': 'Axis Bank',
    'JSWSTEEL': 'JSW Steel',
    'ULTRACEMCO': 'UltraTech Cement',
    'HINDUNILVR': 'Hindustan Unilever',
    'BEL': 'Bharat Electronics',
    'GAIL': 'GAIL India',
    'POWERGRID': 'Power Grid',
    'HAL': 'Hindustan Aeronautics',
    'ONGC': 'ONGC',
    'TATASTEEL': 'Tata Steel',
    'DRREDDY': "Dr. Reddy's",
    'BHARTIARTL': 'Bharti Airtel',
    'COALINDIA': 'Coal India',
    'HDFCBANK': 'HDFC Bank',
    'BRITANNIA': 'Britannia',
    'MRF': 'MRF',
    'BOSCHLTD': 'Bosch',
    'BAJAJ-AUTO': 'Bajaj Auto',
    'EICHERMOT': 'Eicher Motors',
    'SIEMENS': 'Siemens',
    'BPCL': 'BPCL',
    'IPCALAB': 'IPCA Laboratories',
    'ADANIPORTS': 'Adani Ports',
    # NIFTY Next 50
    'ADANIGREEN': 'Adani Green Energy',
    'AMBUJACEM': 'Ambuja Cements',
    'APOLLOHOSP': 'Apollo Hospitals',
    'BAJAJHLDNG': 'Bajaj Holdings',
    'BAJFINANCE': 'Bajaj Finance',
    'BANKBARODA': 'Bank of Baroda',
    'BERGEPAINT': 'Berger Paints',
    'CGPOWER': 'CG Power',
    'CHOLAFIN': 'Cholamandalam',
    'COLPAL': 'Colgate',
    'DABUR': 'Dabur',
    'DLF': 'DLF',
    'DIVISLAB': "Divi's Laboratories",
    'GODREJCP': 'Godrej Consumer',
    'GODREJPROP': 'Godrej Properties',
    'HAVELLS': 'Havells',
    'HDFCLIFE': 'HDFC Life',
    'HINDPETRO': 'Hindustan Petroleum',
    'ICICIPRULI': 'ICICI Prudential',
    'INDHOTEL': 'Indian Hotels',
    'INDUSTOWER': 'Indus Towers',
    'IOC': 'Indian Oil',
    'IRCTC': 'IRCTC',
    'JINDALSTEL': 'Jindal Steel',
    'LTIM': 'LTIMindtree',
    'LUPIN': 'Lupin',
    'MANKIND': 'Mankind Pharma',
    'MARICO': 'Marico',
    'MUTHOOTFIN': 'Muthoot Finance',
    'NAUKRI': 'Naukri',
    'NHPC': 'NHPC',
    'NMDC': 'NMDC',
    'OFSS': 'Oracle Financial',
    'PERSISTENT': 'Persistent Systems',
    'PIDILITIND': 'Pidilite',
    'POLYCAB': 'Polycab',
    'RECLTD': 'REC Limited',
    'SBICARD': 'SBI Cards',
    'SBILIFE': 'SBI Life',
    'SHREECEM': 'Shree Cement',
    'SRF': 'SRF',
    'TATAELXSI': 'Tata Elxsi',
    'TATAPOWER': 'Tata Power',
    'TORNTPOWER': 'Torrent Power',
    'TVSMOTOR': 'TVS Motor',
    'UNITDSPR': 'United Spirits',
    'VBL': 'Varun Beverages',
    'VEDL': 'Vedanta',
    'VOLTAS': 'Voltas',
    'ZYDUSLIFE': 'Zydus',
}

def get_company_name_variations(ticker: str) -> list:
    ticker_clean = ticker.replace('.NS', '')
    variations = [ticker_clean]
    if ticker_clean in COMPANY_NAMES:
        variations.append(COMPANY_NAMES[ticker_clean])
    return variations

def fetch_and_filter_news(db: Session, tickers: list, duration_days: int):
    cutoff_date = datetime.utcnow() - timedelta(days=duration_days)

    for source_name, feed_url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(feed_url)
            if not feed or not feed.entries:
                continue

            for entry in feed.entries:
                try:
                    title = entry.get('title', '').lower()
                    summary = entry.get('summary', '').lower()

                    pub_date_str = entry.get('published', entry.get('updated', ''))
                    try:
                        from email.utils import parsedate_to_datetime
                        pub_date = parsedate_to_datetime(pub_date_str)
                    except:
                        pub_date = datetime.utcnow()

                    if pub_date < cutoff_date:
                        continue

                    for ticker in tickers:
                        company_variations = get_company_name_variations(ticker)

                        match_found = False
                        for variation in company_variations:
                            if variation.lower() in title or variation.lower() in summary:
                                match_found = True
                                break

                        if match_found:
                            existing = db.query(NewsHeadline).filter(
                                NewsHeadline.ticker == ticker,
                                NewsHeadline.headline == entry.get('title', ''),
                                NewsHeadline.source == source_name
                            ).first()

                            if not existing:
                                headline = NewsHeadline(
                                    ticker=ticker,
                                    headline=entry.get('title', '')[:200],
                                    url=entry.get('link', ''),
                                    published_at=pub_date,
                                    source=source_name
                                )
                                db.add(headline)
                except Exception as e:
                    continue

        except Exception as e:
            continue

    db.commit()

def get_news_for_ticker(db: Session, ticker: str, limit: int = 10) -> list:
    headlines = db.query(NewsHeadline).filter(
        NewsHeadline.ticker == ticker
    ).order_by(NewsHeadline.published_at.desc()).limit(limit).all()

    return [
        {
            'headline': h.headline,
            'url': h.url,
            'published_at': h.published_at.isoformat() if h.published_at else '',
            'source': h.source
        }
        for h in headlines
    ]
