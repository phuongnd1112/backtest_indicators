        '''
        # ----- VALUE CHANGES STRATEGY 
        #accumulated value traded over time 
        df['TotalValue'] = [(df.loc[x,'Price'] * df.loc[x,'totalTradingQtty']) if df.loc[x, 'DailyPriceSignal']>0 else -(df.loc[x,'Price'] * df.loc[x,'totalTradingQtty']) for x in df.index]

        df = df.dropna() 
        df['Cum_Value'] = [sum(df.loc[:i, 'TotalValue']) for i in df.index]
        df['%Δ Cum_Value'] = (df['Cum_Value'] - df['Cum_Value'].shift(1)) / df['Cum_Value'].shift(1) * 100 
        df = df.dropna()
        
        print(df)'''