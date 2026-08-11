from new_companies_data import nifty_50
import yfinance as yf
from datetime import date
import requests
import pandas_market_calendars as mcal


nse_cal = mcal.get_calendar('NSE')#gives or handover NSE calender so we can identity when the market is closed or open.
def companys_lists():
    today = date.today().strftime("%Y-%m-%d")
    nse_schedule = nse_cal.schedule(start_date=today,end_date=today)
    
    
    if nse_schedule.empty:
        
        return "Market is closed!"
    company_data = []

    for lists in nifty_50:
        try:

            ticker = yf.Ticker(lists + '.NS')
            data = ticker.history(period="1d",interval="30m")
            if data.empty:
                
                continue
            company_data.append(lists)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            
            return "Error",e
    
    return {"company_lists":company_data}

# companys_lists()



