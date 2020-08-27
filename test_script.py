import yfinance as yf 

class test(): 
    def __init(self, ticker, data): 
        self.ticker = ticker 
        self.data = data 

    def get_Data(self): 
        self.ticker = 'TSLA' 

        ticker_query = yf.Ticker(self.ticker) 

        self.data = ticker_query.history(period='max')

        print(self.data) 

new = test() 
new.get_Data() 

 ma_20_price['DiffMA20/Price'] = [(ma_20_price.loc[i-1, 'MA20']-max_20_price.loc[i-1, 'Price']) + (ma_20_price.loc[i, 'Price']-max_20_price.loc[i-1, 'Price'])]