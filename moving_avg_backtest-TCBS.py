#pip3 install pandas numpy seaborn matplotlib 
#pip install pandas numpy seaborn matplotlib 
#import các lib cần thiết để chạy file 
import tcdata.stock.llv.finance as tcbs
import tcdata.stock.llv.market as tcbs_market 
import tcdata.stock.llv.ticker as tcbs_ticker 
import pandas as pd 
import numpy as np 
import seaborn as sns 
import matplotlib.pyplot as plt 

#script viết thành class để tăng tính tương tác giữa ngừoi chạy và script 
class backtest_indicator_moving_average(): 
    # ------- PART 1: LẤY, SORT VÀ CLEAN DATA 
    def clean_sort_data(self): 
        self.ticker = input('Ticker: ') #ngừoi chạy input ticker vào command line 
        #lấy data
        self.data = tcbs_market.stock_prices([self.ticker], period=2000) #ticker chạy qua db của tcbs, lấy dữ liệu lịch sử 

        #dọn data / sort data
        self.data = self.data.rename(columns = {'openPriceAdjusted': 'Open', 'closePriceAdjusted':'Price'}) #đổi tên cột thành standardised tên (functionality --> nếu có tương tác với db khác )

        #tính daily returns / đánh dấu hiệu mua/bạn dựa theo giao động giá trong ngày 
        self.data['%Δ Daily Returns'] = (self.data['Price']/self.data['Price'].shift(1) - 1) #log return 
        self.data['DailyPriceSignal'] = [1 if self.data.loc[x, '%Δ Daily Returns'] > 0 else -1 for x in self.data.index] #1 là mua, -1 là bán 

    # ----- PART 2: MUA/BÁN THEO TÍN HIỆU MA  
    def calculate_moving_average(self): 
        self.ma = pd.DataFrame() #tạo df mới để xét dữ liệu dễ hơn
        self.ma['Date'] = self.data['dateReport'] #kéo dữ liệu từ df self.data sang bên self.ma 
        self.ma['%Δ Daily Returns'] = self.data['%Δ Daily Returns']
        self.ma['Price'] = self.data['Price']

        #dùng method rolling and mean để tính moving averages 
        self.ma['MA20'] = self.data['Price'].rolling(20).mean() 
        self.ma['MA50'] = self.data['Price'].rolling(50).mean()
        self.ma['MA100'] = self.data['Price'].rolling(100).mean()

        self.ma = self.ma.dropna() #xoá na vì có một vài cell sẽ trả NaN do không đủ cell rolling để tính mean 

        #đánh tín hiệu mua/bán dựa theo điểm cắt của các cặp MA/Giá khác nhau 
        #logic: 1 (mua) nếu MA(bé) cắt MA(lớn) giữa 2 phiên 
        self.ma['Buy_MA20/Price'] = [1 if (self.ma.loc[i, 'MA20'] > self.ma.loc[i, 'Price']) and (self.ma.loc[i+1, 'MA20'] < self.ma.loc[i+1,'Price']) else -1 for i in self.ma.index] #MA20/Close 

        self.ma['Buy_MA50/MA20'] = [1 if (self.ma.loc[i, 'MA50'] > self.ma.loc[i, 'MA20']) and (self.ma.loc[i+1, 'MA50'] < self.ma.loc[i+1, 'MA20']) else -1 for i in self.ma.index] #MA50/MA20 

        self.ma['Buy_MA100/MA50'] = [1 if (self.ma.loc[i, 'MA100'] > self.ma.loc[i, 'MA50'] and (self.ma.loc[i+1, 'MA100']) < self.ma.loc[i+1, 'MA50']) else -1 for i in self.ma.index] #MA100/50

        #exploratory analysis shows that MA20/Price seems to be the strongest signal 
    
    ## ---- PART 3: Lọc data cho thấy duy nhất tín hiệu mua, tính khả năng lãi/lỗ tối thiếu + % lỗ (mặc dù tín hiệu báo mua) 
    def ma_single_strat(self): #this function takes the MA indicators individually and use them as indicator 

        self.start_list = ['Buy_MA20/Price', 'Buy_MA50/MA20', 'Buy_MA100/MA50'] #tạo list cho cặp tín hiệu 

        self.ma['%Δ Daily ReturnsLAG1'] = self.ma['%Δ Daily Returns'].shift(1) #vì khi tính tín hiệu, tín hiệu được đánh theo ngày hôm sau ([i+1]) --> shift một ngày để xem sác xuất trong phiên ĐÃ được tín hiệu báo 

        for s in self.start_list: #loop qua list để xem sác xuất từng cặp một
            ma_single_strat = pd.DataFrame() #tạo df rỗng
            for i in self.ma.index: #với mỗi ngày trong data ma 
                if self.ma.loc[i, s] > 0: #nếu tín hiệu báo mua 
                    ma_single_strat = ma_single_strat.append(self.ma.loc[i,:]) #append list báo dấu hiệu MUA với duy nhất những điểm báo mua 
                else: 
                    pass
            
            #với mỗi cặp tín hiệu, xem qua một vài thông số 
            result_list = [] #tạo một list để store kết quả 
            result_list.append(self.ticker) #append với ticker 
            result_list.append(s) #append với cặp tín hiệu 

            #lãi cao nhất với tín hiệu báo mua 
            max_return_strat = ma_single_strat['%Δ Daily ReturnsLAG1'].max() #tìm max daily return (lag1) 
            result_list.append(max_return_strat) #append vào list kết quả 

            #lỗ cao nhất với tín hiệu báo mua 
            max_loss_strat = ma_single_strat['%Δ Daily ReturnsLAG1'].min() 
            result_list.append(max_loss_strat)

            #return trung bình 
            return_avg = ma_single_strat['%Δ Daily ReturnsLAG1'].mean() 
            result_list.append(return_avg)

            #tổng số ngày lỗ với tín hiệu mua 
            neg_return_count = 0 
            for i in ma_single_strat.index: #với mỗi điểm data 
                if ma_single_strat.loc[i, '%Δ Daily ReturnsLAG1'] < 0: #nếu return <0% 
                    neg_return_count += 1 #cộng thêm một count vào tổng số ngày lỗ 
            result_list.append(neg_return_count)

            #sác xuất lỗ với tín hiệu mua 
            loss_prob = neg_return_count / len(ma_single_strat['Price'].values.tolist())
            result_list.append(loss_prob)

            print("Ticker, tín hiệu báo, lãi max, max lỗ, return trung bình, số ngày lỗ, %lỗ.")
            print(result_list) 


    def ma_single_strat_lag(self): 
        self.ma['%Δ Daily ReturnsLAG2'] = self.ma['%Δ Daily Returns'].shift(2) #vì khi tính tín hiệu, tín hiệu được đánh theo ngày hôm sau ([i+1]) --> shift một ngày để xem sác xuất trong phiên ĐÃ được tín hiệu báo 

        for s in self.start_list: #loop qua list để xem sác xuất từng cặp một
            ma_single_strat = pd.DataFrame() #tạo df rỗng
            for i in self.ma.index: #với mỗi ngày trong data ma 
                if self.ma.loc[i, s] > 0: #nếu tín hiệu báo mua 
                    ma_single_strat = ma_single_strat.append(self.ma.loc[i,:]) #append list báo dấu hiệu MUA với duy nhất những điểm báo mua 
                else: 
                    pass
            
            #với mỗi cặp tín hiệu, xem qua một vài thông số 
            result_list = [] #tạo một list để store kết quả 
            result_list.append(self.ticker) #append với ticker 
            result_list.append(s) #append với cặp tín hiệu 

            #lãi cao nhất với tín hiệu báo mua 
            max_return_strat = ma_single_strat['%Δ Daily ReturnsLAG2'].max() #tìm max daily return (lag1) 
            result_list.append(max_return_strat) #append vào list kết quả 

            #lỗ cao nhất với tín hiệu báo mua 
            max_loss_strat = ma_single_strat['%Δ Daily ReturnsLAG2'].min() 
            result_list.append(max_loss_strat)

            #return trung bình 
            return_avg = ma_single_strat['%Δ Daily ReturnsLAG2'].mean() 
            result_list.append(return_avg)

            #tổng số ngày lỗ với tín hiệu mua 
            neg_return_count = 0 
            for i in ma_single_strat.index: #với mỗi điểm data 
                if ma_single_strat.loc[i, '%Δ Daily ReturnsLAG2'] < 0: #nếu return <0% 
                    neg_return_count += 1 #cộng thêm một count vào tổng số ngày lỗ 
            result_list.append(neg_return_count)

            #sác xuất lỗ với tín hiệu mua 
            loss_prob = neg_return_count / len(ma_single_strat['Price'].values.tolist())
            result_list.append(loss_prob)

            print("(LAG) Ticker, tín hiệu báo, lãi max, max lỗ, return trung bình, số ngày lỗ, %lỗ.")
            print(result_list) 

new = backtest_indicator_moving_average() 
new.clean_sort_data() 
new.calculate_moving_average() 
new.ma_single_strat() 
new.ma_single_strat_lag()