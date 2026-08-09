import yfinance as yf
from types import SimpleNamespace
nifty_50 ={}

nifty_50['IT'] = ["INFY","TCS","HCLTECH","TECHM","WIPRO"]
nifty_50["Banking"] = ["HDFCBANK","ICICIBANK","KOTAKBANK","SBIN","AXISBANK"]
nifty_50["Finance"] = ["BAJFINANCE","BAJAJFINSV","SHRIRAMFIN","HDFCLIFE","SBILIFE","JIOFIN"]
nifty_50['Automobile'] = ["BAJAJ-AUTO", "HEROMOTOCO", "M&M", "MARUTI", "TATAMOTORS","EICHERMOT"]
nifty_50['Energy'] = ["RELIANCE","ONGC","POWERGRID","COALINDIA","NTPC"]
nifty_50['Metals'] = ["TATASTEEL","JSWSTEEL","HINDALCO"]
nifty_50['Pharma'] = ["APOLLOHOSP","CIPLA","DRREDDY","SUNPHARMA"]
nifty_50['FMCG'] = ["HINDUNILVR","ITC","NESTLEIND","TATACONSUM"]
nifty_50['Consumer_Durables'] = ["ASIANPAINT","TITAN"]
nifty_50['Retail'] = ["TRENT","ETERNAL"]
nifty_50['Telecom'] = ["BHARTIARTL"]
nifty_50['Defence']= ["BEL", "LT"]
nifty_50['Construction'] = ["GRASIM","ULTRACEMCO"]
nifty_50['Services_Infrastructure'] = ["ADANIPORTS"]

def get_sector(sector_name):#RELIANCE
    
    for k,v in nifty_50.items():
        try:
            if sector_name in v:#RELIANCE 
                return k#will return OIL & ENERGY 
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
    #so output will be IT:{current_price:345,high:high,low:low} if we have two stocks from IT than it will sum-up that that two current prices of wipro and infosys and result will be same which explains how much holding has been made in the IT sector by user.
test_namesspace = SimpleNamespace(stock_name="RELIANCE",quantity=1,buy_price=2890)

identify_the_sector([test_namesspace])








    













