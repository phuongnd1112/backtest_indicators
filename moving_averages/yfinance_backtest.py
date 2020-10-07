#ANALYSING AND BACKTESTING MOVING AVERAGES AS TRADING STRATEGIES 
#INSTALL LIBRARIES 
#pip3 install yfinance pandas seaborn matplotlib
#pip install yfinance pandas seaborn matplotlib 
import yfinance as yf 
import pandas as pd 
import seaborn as sns 
import matplotlib.pyplot as plt 
import numpy as np 
from scipy.stats import norm

class backtest_ma_yf():  
    #self --> maintain variables throughout the whole class (because usually, variables pertain only to the function in which it belons to)
    def __init__(self, ticker): 
        self.ticker = ticker #initiating an init class for ticker because ticker use prompted must be inserted 

    ## ---- PART 1: function to clean, sort and process necessary data for analysis 
    def get_clean_data(self): 
        ticker = yf.Ticker(self.ticker) #using yFinance to get data on ticker [open, close, volume]

        self.data = ticker.history(period='max') #get maximum period, subjected to development if start/end --> parameters 
        self.data = self.data.reset_index(inplace=False) #functionality issue, reset index as 0,1,2,3,...

        self.data['%Δ Daily Returns'] = (self.data['Close']/self.data['Close'].shift(1) - 1) #calculate log daily returns 
        self.data['DailyPriceSignal'] = [1 if self.data.loc[x, '%Δ Daily Returns'] > 0 else -1 for x in self.data.index] #based on log daily returns, determine whether this is a good buy (-1 means sell, 1 means buy) 
        print(self.data) 
    
    ## ---- PART 2: this function calculates moving averages and set buy/sell signals
    def calculate_moving_averages(self, timeframe):  
        self.ma = pd.DataFrame() #create a new DataFrame for clarity purposes 
        self.ma['Date'] = self.data['Date'] #transferring data from self.data
        self.ma['Price'] = self.data['Close']
        self.ma['%Δ Daily Returns'] = self.data['%Δ Daily Returns']
        self.ma['MA'+timeframe] = self.data['Close'].rolling(timeframe).mean() #calculate moving averages by using .rolling(insert MA).mean() 
       
        self.ma = self.ma.dropna() #some cells will return NaN value because of the rolling method. Delete these to avoid errors in further processing 

        print(self.ma) 

        #assigning signals using different MA/Price combinations 
        #logical process: 1 (for buy) if smaller-window signal turns from negative to positive tomorrow (e.g: 1 if Price cuts MA20 tomorrow)
        self.ma['Buy_MA20/Price'] = [1 if (self.ma.loc[i, 'MA20'] > self.ma.loc[i, 'Price']) and (self.ma.loc[i+1, 'MA20'] < self.ma.loc[i+1,'Price']) else -1 for i in self.ma.index] #MA20/Close

        self.ma['Buy_MA50/MA20'] = [1 if (self.ma.loc[i, 'MA50'] > self.ma.loc[i, 'MA20']) and (self.ma.loc[i+1, 'MA50'] < self.ma.loc[i+1, 'MA20']) else -1 for i in self.ma.index] #MA50/MA20

        self.ma['Buy_MA100/MA50'] = [1 if (self.ma.loc[i, 'MA100'] > self.ma.loc[i, 'MA50'] and (self.ma.loc[i+1, 'MA100']) < self.ma.loc[i+1, 'MA50']) else -1 for i in self.ma.index] #MA100/50

        #exploratory analysis shows that MA20/Price seems to be the strongest signal 

    ## ---- PART 3: this function filters data by selecting only positive buy signals, and calculate max/min returns + probability that it buyers make a loss 
    def ma_single_strat(self): 
        self.start_list = ['Buy_MA20/Price', 'Buy_MA50/MA20', 'Buy_MA100/MA50'] #create list for signal pairs 

        self.ma['%Δ Daily ReturnsLAG1'] = self.ma['%Δ Daily Returns'].shift(1) #shift returns one day down because we've set signal as 'tomorrow' with [i+1]

        for s in self.start_list: #loop through list to examine each signal 
            ma_single_strat = pd.DataFrame() #empty dataframe to store results
            for i in self.ma.index: #with each day in our dataset  
                if self.ma.loc[i, s] > 0: #if the signal says buy 
                    ma_single_strat = ma_single_strat.append(self.ma.loc[i,:]) #append list with data of only buy days 
                else: 
                    pass
            
            #with each signal, compile a list of important nums 
            result_list = [] #empty list to store results 
            result_list.append(self.ticker) #append with ticker 
            result_list.append(s) #append with signal 

            #highest returns 
            max_return_strat = ma_single_strat['%Δ Daily ReturnsLAG1'].max() #find maximum returns 
            result_list.append(max_return_strat) #append list with res  

            #lowest returns/highest loss
            max_loss_strat = ma_single_strat['%Δ Daily ReturnsLAG1'].min() 
            result_list.append(max_loss_strat)

            #mean returns 
            return_avg = ma_single_strat['%Δ Daily ReturnsLAG1'].mean() 
            result_list.append(return_avg)

            #total incidents of loss despite buy signals 
            neg_return_count = 0 
            for i in ma_single_strat.index: #with each data point  
                if ma_single_strat.loc[i, '%Δ Daily ReturnsLAG1'] < 0: #if return <0% 
                    neg_return_count += 1 #add one count to total negative return counts  
            result_list.append(neg_return_count)

            #% probability of loss despite a buy signal 
            loss_prob = neg_return_count / len(ma_single_strat['Price'].values.tolist())
            result_list.append(loss_prob)

            print("Ticker, signal, max returns, max loss, average returns, #in with neg returns, Prob Loss.")
            print(result_list)  

            mu = self.ma['%Δ Daily ReturnsLAG1'].mean() 
            sigma = self.ma['%Δ Daily ReturnsLAG1'].std(ddof=1) 

            def probability(lst): 
                likelihood = pd.DataFrame()
                likelihood['Loss/Gain'] = lst 
                likelihood = likelihood.set_index('Loss/Gain')
                values_list = [] 
                for i in lst: 
                    value = norm.cdf((i/100), mu, sigma) 
                    if i > 0: 
                        value = 1 - value #because the PDF / CDF calculates the total area up to value, subtract from 1  
                    values_list.append(value)
                likelihood['%'] = values_list  
                print(s)
                print(likelihood) 
            
            gain_range = np.arange(1, 11, 1) 
            loss_range = np.arange(-10, 0, 1) 
            probability(loss_range)
            probability(gain_range)

    ## ---- PART 4: this function filters data by selecting only positive buy signals, and calculate max/min returns + probability that it buyers make a loss considering a one-day lag in price changes 
    def ma_single_strat_lag(self): 
        self.ma['%Δ Daily ReturnsLAG2'] = self.ma['%Δ Daily Returns'].shift(2) #shift returns two day down because we've set signal as 'tomorrow' with [i+1] -- examine with some lagging factor

        for s in self.start_list: #loop through list to examine each signal 
            ma_single_strat = pd.DataFrame() #empty dataframe to store results
            for i in self.ma.index: #with each day in our dataset  
                if self.ma.loc[i, s] > 0: #if the signal says buy 
                    ma_single_strat = ma_single_strat.append(self.ma.loc[i,:]) #append list with data of only buy days 
                else: 
                    pass
            
            #with each signal, compile a list of important nums 
            result_list = [] #empty list to store results 
            result_list.append(self.ticker) #append with ticker 
            result_list.append(s) #append with signal 

            #highest returns 
            max_return_strat = ma_single_strat['%Δ Daily ReturnsLAG2'].max() #find maximum returns 
            result_list.append(max_return_strat) #append list with res  

            #lowest returns/highest loss
            max_loss_strat = ma_single_strat['%Δ Daily ReturnsLAG2'].min() 
            result_list.append(max_loss_strat)

            #mean returns 
            return_avg = ma_single_strat['%Δ Daily ReturnsLAG2'].mean() 
            result_list.append(return_avg)

            #total incidents of loss despite buy signals 
            neg_return_count = 0 
            for i in ma_single_strat.index: #with each data point  
                if ma_single_strat.loc[i, '%Δ Daily ReturnsLAG2'] < 0: #if return <0% 
                    neg_return_count += 1 #add one count to total negative return counts  
            result_list.append(neg_return_count)

            #% probability of loss despite a buy signal 
            loss_prob = neg_return_count / len(ma_single_strat['Price'].values.tolist())
            result_list.append(loss_prob)

            print("(LAG) Ticker, signal, max returns, max loss, average returns, #in with neg returns, Prob Loss.")
            print(result_list)

            mu = self.ma['%Δ Daily ReturnsLAG2'].mean() 
            sigma = self.ma['%Δ Daily ReturnsLAG2'].std(ddof=1) 

            def probability(lst): 
                likelihood = pd.DataFrame()
                likelihood['Loss/Gain'] = lst 
                likelihood = likelihood.set_index('Loss/Gain')
                values_list = [] 
                for i in lst: 
                    value = norm.cdf((i/100), mu, sigma) 
                    if i > 0: 
                        value = 1 - value #because the PDF / CDF calculates the total area up to value, subtract from 1  
                    values_list.append(value)
                likelihood['%'] = values_list  
                print(s)
                print(likelihood) 
            
            gain_range = np.arange(1, 11, 1) 
            loss_range = np.arange(-10, 0, 1) 
            probability(loss_range)
            probability(gain_range)

user_ticker=input('Ticker?: ')
a = backtest_ma_yf(user_ticker) 
a.get_clean_data()
a.calculate_moving_averages()
a.ma_single_strat() 
a.ma_single_strat_lag()
