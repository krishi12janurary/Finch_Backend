import yfinance as yf
from new_companies_data import nifty_50

def fetching_current_price(company_symbol):
    prices = []
    yes_there = [s for s in company_symbol if s in nifty_50]#without NS
    if not yes_there:
        
        return None
    comp_symbol = [s + ".NS" for s in yes_there]#with .NS
    try:
        data = yf.download(comp_symbol,period='1d',interval='1m', group_by='ticker',progress=False)# one with .NS is the company name which yfinance will understand of which company the user is talking becuase yfinance has stored their company names with .NS symbol once we get that we will stored it 
        for symbol,without_symbol in zip(comp_symbol,yes_there):#we need both one with .NS for yfinance and one without .NS for forntend and backend understanding. becuase if we use one than either finance will not unerstand or frontend or backend will not understand
            try:
                if 'Close' in data:
                    current_price = data['Close']#here we are handling multiple and single stock handling becuase earlier even if user has one investment than yf.download could not able to handle it due to which here we are diversifying risk by telling if user has only single ticker as investment than take out their close price only and if user has multiple ticker investments than hadle the elif statement which alter with checking like symbol exsits in the data and if yes than does close exsits and yes than store the price in current price and give it so even both fails or either one fails the else block with nodata found will get execute.ohhhh so we can understand than when there will be multiple investments than only the dataframe will be grouped by and data[symbol] will be get considered otherwise if user has only one invrstment than the grouping will happening but there will be no data[symbol] wala key be created? correct? due to which the erroor has been occured.
                elif symbol in data and 'Close' in data[symbol]:
                    current_price = data[symbol]['Close']#while when user has multiple investments the df.download dataframe will create data['symbol'] as well and than check the close price for that symbol exists in that frame or not and than the process will be executing
                else:
                    
                    continue

                
                if current_price is None:
                    
                    continue

                price = current_price.iloc[-1]                
                prices.append({"company":without_symbol,
                               "current_price":float(price)})
                
            except Exception as e:
                
                return None

        return prices
            

    except Exception as e:
        
        return None

# fetching_current_price(["RELIANCE","WIPRO"])


