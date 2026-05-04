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
    'RELIANCE': 'Reliance Industries',
    'HDFCBANK': 'HDFC Bank',
    'BHARTIARTL': 'Bharti Airtel',
    'SBIN': 'State Bank of India',
    'ICICIBANK': 'ICICI Bank',
    'TCS': 'Tata Consultancy Services',
    'BAJFINANCE': 'Bajaj Finance',
    'LT': 'Larsen & Toubro',
    'HINDUNILVR': 'Hindustan Unilever',
    'INFY': 'Infosys',
    'SUNPHARMA': 'Sun Pharmaceutical',
    'MARUTI': 'Maruti Suzuki',
    'ADANIPORTS': 'Adani Ports',
    'AXISBANK': 'Axis Bank',
    'ITC': 'ITC',
    'TITAN': 'Titan',
    'KOTAKBANK': 'Kotak Mahindra Bank',
    'ONGC': 'ONGC',
    'ULTRACEMCO': 'UltraTech Cement',
    'ADANIENT': 'Adani Enterprises',
    'HCLTECH': 'HCL Technologies',
    'BEL': 'Bharat Electronics',
    'JSWSTEEL': 'JSW Steel',
    'POWERGRID': 'Power Grid',
    'COALINDIA': 'Coal India',
    'BAJAJ-AUTO': 'Bajaj Auto',
    'BAJAJFINSV': 'Bajaj Finserv',
    'NESTLEIND': 'Nestle India',
    'TATASTEEL': 'Tata Steel',
    'ASIANPAINT': 'Asian Paints',
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
