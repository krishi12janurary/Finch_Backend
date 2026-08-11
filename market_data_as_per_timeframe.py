

from new_companies_data import nifty_50
import yfinance as yf
import requests

def converting_dict_to_orients(df):
    df = df.copy()
    df.index = df.index.astype(str)
    return df.reset_index().to_dict(orient='records')

   
    
def fetching_50_companies():
    
    
    
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
            
            return "Internal connection Error, this error is from NSE side so please cooperate."
        
        except Exception as e:
            
            return "Error",e

             
    
    return results
    

# fetching_50_companies()




