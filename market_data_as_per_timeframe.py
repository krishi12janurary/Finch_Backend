


import yfinance as yf
import requests

def converting_dict_to_orients(df):
    df = df.copy()
    df.index = df.index.astype(str)
    return df.reset_index().to_dict(orient='records')

   
    
def fetching_50_companies():
    
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
    
    results = {}
       

    for symbol in nifty_50:
        try:
            ticker = yf.Ticker(symbol + '.NS')
            data_1day = ticker.history(period="1d", interval="15m")
            data_5days = ticker.history(period="5d",interval="1h")
            data_1week = ticker.history(period="7d",interval="1h")
            data_1month = ticker.history(period='1mo',interval="1d")
            data_3month = ticker.history(period='3mo', interval='1d')
            data_1year = ticker.history(period='1y',interval='1mo')
                
            if data_5days.empty or data_1week.empty:
                print("Data is empty")
                continue
            data_1day.index = data_1day.index.astype(str)   
            data_5days.index = data_5days.index.astype(str)
            data_1week.index = data_1week.index.astype(str)
            data_1month.index = data_1month.index.astype(str)
            data_3month.index = data_3month.index.astype(str)
            data_1year.index = data_1year.index.astype(str)  
            results[symbol] = {
                "1day":converting_dict_to_orients(data_1day),
                "5days":converting_dict_to_orients(data_5days),
                "1week":converting_dict_to_orients(data_1week),
                "1month":converting_dict_to_orients(data_1month),
                "3month":converting_dict_to_orients(data_3month),
                "1year":converting_dict_to_orients(data_1year)
                    
            }
            
                
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            print("Internal connection Error, this error is from NSE side so please cooperate.")
            return "Internal connection Error, this error is from NSE side so please cooperate."
        
        except Exception as e:
            print("Internal Server Error")
            return "Error",e

             
    print("Data is delivered")
    return results
    

fetching_50_companies()



# data = yf.Ticker("RELIANCE.NS")
# history = data.history(period="1d",interval="1m")
# print(history)


