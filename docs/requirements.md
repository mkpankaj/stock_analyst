\# Project Overview

Web application which can run across all devices (desktop, laptop,
tablets and mobile). The application will be used to fetch stock price,
do advanced analysis to extract key insights with regards to stock
performance and scrape the internet to retrieve news or information
which could have influenced the stock prices in past or can influence
the price in near future.

\# Key features of Application

- User registration page: user will register himself using email or
  phone number

- Home page: will show the most recent analysis of stocks

- Configuration page: user will configure the search parameters and
  schedule the analysis. Duration on Configuration page can't be more
  than 120 days.

- Analysis will be triggered automatically according to parameters on
  configuration page. User can trigger the analysis manually by clicking
  on Analysis button on home page.

- Analysis will be stored in database. Only one analysis will be stored
  per date. If user changes the parameter and runs the analysis on same
  date then overwrite the previous analysis of the same date. Only one
  analysis for a date will be stored in database.

- User can search the past analysis as per date

- Once the stock price is fetched, store the data in database. Next
  time, the application will fetch stock price since the last date when
  it was fetched. Application will fetch only incremental data since the last fetch.

- Daily stock price will be saved in database. When user clicks on a
  stock, chart will show weekly price.

\# Workflow

- User will land on login page. First time user will register himself
  using email or phone nbr

- User will land on home page. First time user will see blank screen and
  will have to configure the parameters to trigger analysis.

- Home page will show the latest analysis.

- User can manually trigger analysis from home page. Application will
  read the parameters settings to trigger the analysis.

- When user triggers the analysis, UI should show the progress. If there
  is failure then show message on screen "Process failed. Please retry"

\# Business Logic of Stock Analysis

- read parameter settings

- fetch stock price from Yahoo Finance (https://finance.yahoo.com/quote/%5ENSEI/) as per
  parameter settings. For ex:

> import yfinance as yf
>
> Fetch Reliance Industries stock data
>
> reliance = yf.Ticker(\"RELIANCE.NS\")
>
> Get current price
>
> price = reliance.history(period=\"1d\")\[\'Close\'\].iloc\[-1\]

- Drop the stock if less than 80% data is available

- analyze the stock price to find Top 10 gainers and Top 10 losers in
  last 4 months. Price change will be calculated between D1 and D120.
  For ex: D1 -- Rs 100, D120 -- Rs 118. Price change is 18%
  (118-100)/100

- For ex: Top Gainers: stocks whose prices have increased the maximum
  from D1 to D120

- Top Losers: stocks whose prices have decreased the maximum from D1 to
  D120.

- scrape prominent business news websites in India like Business
  Standard, Mint, Financial Express and Economic Times to search news of
  last 4 months having Company Name in the headline of news. Show the
  headline and provide link of source.

- When user clicks on any of the 20 stocks, a new screen will open up.
  It will show the stock price movement in top half of screen and news
  in lower half of screen.

- Stock price movement for last 4 months will be shown on a weekly
  timeline. Median price of the stock for a week will be taken as weekly
  price. If the number of days are less than a week for any reason then
  still take median price of available days.

- If the price of stock has increased from D1 to D120 and is overall
  slope is increasing for last 30 days then show Strong Upward trend
  label.

For ex: D1: Rs 100, D90: Rs 105, D120: Rs 118. Price has increased from
D1 to D120. Price has consistently increased in last 30 days from D90 to
D120. Hence Strong Upward trend ![Bar graph with upward
trend](media/image2.svg){width="0.20586832895888013in"
height="0.20586832895888013in"}

- If the price of stock has increased from Day 1 to Day 120 but the
  price for last 30 days hasn't changed more than 4% then show Weak
  Uptrend. ![Upward
  trend](media/image4.svg){width="0.2305161854768154in"
  height="0.2305161854768154in"}

For ex: D1: Rs 100, D90: Rs 105, D120: Rs 109. Price has increased from
D1 to D120 but the price hasn't changed more than 4% in last 30 days.
Hence Weak Upward trend.

- If the price of stock has decreased from Day 1 to Day 120 and the
  overall slope is decreasing from Day 90 to Day 120 then show Strong
  Downward trend.![Bar graph with downward
  trend](media/image6.svg){width="0.19693897637795277in"
  height="0.19693897637795277in"}

\# Failure Handling:

- if API call fails then abort the process and show message to user to
  retry.

- if news scraping fails then continue. Show the analysis without news
  on screen.

\# Dashboard

- User clicks My Dashboard to open the dashboard page.

- Dashboard page will show the latest stock analysis by default.

- User can select date to see the historical analysis. System will fetch
  the historical analysis from database.

This product is a MVP to test the concept with minimal feature with 1-2
users. Therefore, I want to keep the technology stack very simple, easy
to maintain and open source or free one.
