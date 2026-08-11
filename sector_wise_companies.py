import yfinance as yf

from new_companies_data import nifty_50_by_sector

def get_sector(sector_name):
    
    for k,v in nifty_50_by_sector.items():
        try:
            if sector_name in v:
                return k
        except Exception as e:
            return "Error has been occured",e
    return "Unknown"

def identify_the_sector(user_investments):

    sector_totals = {}

    for record in user_investments:
        ticker = record.stock_name#RELIANCE
        sector = get_sector(ticker)#find RELIANCE and than will return the sector like energy

        stock = yf.Ticker(f"{ticker}.NS")
        stock_history = stock.history("1d")

        current_price = stock_history['Close'].iloc[-1]
        day_high = stock_history['High'].iloc[-1]
        day_low = stock_history['Low'].iloc[-1]

        
        current_stock_value = current_price * record.quantity

        if sector not in sector_totals:
            sector_totals[sector] = {"current_value":0,"high":0,"low":0}
        
        sector_totals[sector]['current_value'] += current_stock_value
        sector_totals[sector]['high'] += day_high
        sector_totals[sector]['low'] += day_low
    
    response_formated_data = [
        {"sector":sector,"current_value":data['current_value'],"high":data['high'],"low":data['low']}
        for sector,data in sector_totals.items()
    ] 
    return response_formated_data#okay so  currently i am holding 2 wipro shares and one ITC share so wipro will be of IT and ITC will be FMCG so current_price of wipro is 178 * 2  = whatever will eb answer will says you contributed or your stake in these or holding in these sector is 356 and same as ITC.
    








    













