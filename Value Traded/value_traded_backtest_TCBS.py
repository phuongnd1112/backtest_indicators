import tcdata.stock.llv.finance as tcbs
import tcdata.stock.llv.market as tcbs_market 
import tcdata.stock.llv.ticker as tcbs_ticker 
import pandas as pd 
import numpy as np 
import seaborn as sns 
import matplotlib.pyplot as plt 

class backtest_indicator_value_traded(): 
    # ------- PART 1: LẤY, SORT VÀ CLEAN DATA 
    def clean_sort_data(self): 
        self.ticker = input('Ticker: ') #ngừoi chạy input ticker vào command line 
        #lấy data
        self.data = tcbs_market.stock_prices([self.ticker], period=2000) #ticker chạy qua db của tcbs, lấy dữ liệu lịch sử 

        #dọn data / sort data
        self.data = self.data.rename(columns = {'openPriceAdjusted': 'Open', 'closePriceAdjusted':'Close'}) #đổi tên cột thành standardised tên (functionality --> nếu có tương tác với db khác ) // price = close 
        self.data = self.data.sort_values('dateReport', ascending = True)

        #tính daily returns / đánh dấu hiệu mua/bạn dựa theo giao động giá trong ngày 
        self.data['%Δ Daily Returns'] = (self.data['Close']/self.data['Close'].shift(1) - 1) #log return 
        self.data['DailyPriceSignal'] = [1 if self.data.loc[x, '%Δ Daily Returns'] > 0 else -1 for x in self.data.index] #1 là mua, -1 là bán 

    def calculated_traded_value(self): 
        # ----- VALUE CHANGES STRATEGY 
        #accumulated value traded over time 
        self.data['TotalValue'] = [(self.data.loc[i,'Close'] * self.data.loc[i,'totalTradingQtty']) if self.data.loc[i, 'DailyPriceSignal'] > 0 else -(self.data.loc[i,'Close'] * self.data.loc[i,'totalTradingQtty']) for i in self.data.index]

        self.data = self.data.dropna() 
        self.data['Cum_Value'] = [sum(self.data.loc[:i, 'TotalValue']) for i in self.data.index]
        self.data['%Δ Cum_Value'] = (self.data['Cum_Value'] - self.data['Cum_Value'].shift(1)) / self.data['Cum_Value'].shift(1) * 100 
        self.data = self.data.dropna()

        print(self.data)
    
    def value_traded_strat(self): 
        value_traded_strat = pd.DataFrame() 
        for i in self.data.index: 
            if self.data.loc[i, 'Cum_Value'] > 0: 
                value_traded_strat = value_traded_strat.append(self.data.loc[i, :])
            else: 
                pass 
        print(value_traded_strat) 

        

new = backtest_indicator_value_traded() 
new.clean_sort_data() 
new.calculated_traded_value() 
new.value_traded_strat()