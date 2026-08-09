import yfinance as yf
from datetime import date
import requests
import pandas_market_calendars as mcal

nse_cal = mcal.get_calendar('NSE')#gives or handover NSE calender so we can identity when the market is closed or open.
def companys_lists():
    today = date.today().strftime("%Y-%m-%d")
    nse_schedule = nse_cal.schedule(start_date=today,end_date=today)
    
    nifty_50 = [
        
        "ADANIENT", "ADANIPORTS", "APOLLOHOSP", "ASIANPAINT", "AXISBANK",
        "BAJAJ-AUTO", "BAJFINANCE", "BAJAJFINSV", "BEL", "BHARTIARTL",
        "CIPLA", "COALINDIA", "DRREDDY", "EICHERMOT", "ETERNAL",
        "GRASIM", "HCLTECH", "HDFCBANK", "HDFCLIFE", "HEROMOTOCO",
        "HINDALCO", "HINDUNILVR", "ICICIBANK", "ITC", "INDUSINDBK",
        "INFY", "JSWSTEEL", "JIOFIN", "KOTAKBANK", "LT",
        "M&M", "MARUTI", "NTPC", "NESTLEIND", "ONGC",
        "POWERGRID", "RELIANCE", "SBILIFE", "SHRIRAMFIN", "SBIN",
        "SUNPHARMA", "TCS", "TATACONSUM", "TATAMOTORS", "TATASTEEL",
        "TECHM", "TITAN", "TRENT", "ULTRACEMCO", "WIPRO"
    ]
    if nse_schedule.empty:
        print("Market is closed!")
        return "Market is closed!"
    company_data = []

    for lists in nifty_50:
        try:

            ticker = yf.Ticker(lists + '.NS')
            data = ticker.history(period="1d",interval="30m")
            if data.empty:
                print("Failed to fetch companys")
                continue
            company_data.append(lists)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            print("Error")
            return "Error",e
    print("Company's Data has been submitted")
    return {"company_lists":company_data}

companys_lists()



