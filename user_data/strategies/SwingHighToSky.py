from freqtrade.strategy.interface import IStrategy
from typing import Dict, List
from functools import reduce
from pandas import DataFrame

import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
import numpy
from freqtrade.strategy import IntParameter, CategoricalParameter

# __author__      = "Kevin Ossenbrück"
# __copyright__   = "Free For Use"
# __credits__     = ["Bloom Trading, Mohsen Hassan"]
# __license__     = "MIT"
# __version__     = "1.0"
# __maintainer__  = "Kevin Ossenbrück"
# __email__       = "kevin.ossenbrueck@pm.de"
# __status__      = "Live"

# # CCI timerperiods and values
# cciBuyTP = 72
# cciBuyVal = -175
# cciSellTP = 66
# cciSellVal = -106

# # RSI timeperiods and values
# rsiBuyTP = 36
# rsiBuyVal = 90
# rsiSellTP = 45
# rsiSellVal = 88
    
class SwingHighToSky(IStrategy):

    minimal_roi = {
        "0": 0.496,
        "294": 0.074,
        "807": 0.025,
        "1122": 0
    }
    stoploss = -0.229
    timeframe = '1h'
    # Trailing stop:
    trailing_stop = True
    trailing_stop_positive = 0.225
    trailing_stop_positive_offset = 0.282
    trailing_only_offset_is_reached = False

    cci_TP=IntParameter(50,90, default=60,space='buy')
    rsi_TP=IntParameter(20,60, default=58,space='buy')

    buy_cci_Value=IntParameter(-200,-100, default=-186,space='buy')
    buy_rsi_Value=IntParameter(5,50, default=35,space='buy')
    buy_cci_enabled=CategoricalParameter([True,False],default=True,space='buy')
    buy_rsi_enabled=CategoricalParameter([True,False],default=True,space='buy')

    sell_cci_Value=IntParameter(100,200, default=116,space='sell')
    sell_rsi_Value=IntParameter(60,100, default=95,space='sell')
    sell_cci_enabled=CategoricalParameter([True,False],default=True,space='sell')
    sell_rsi_enabled=CategoricalParameter([True,False],default=True,space='sell')

    

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        for val in self.cci_TP.range:
            dataframe['cci-'+str(val)] = ta.CCI(dataframe, timeperiod=val)
        for val in self.rsi_TP.range:
            dataframe['rsi-'+str(val)] = ta.RSI(dataframe, timeperiod=val)
        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions=[]
        if self.buy_cci_enabled.value:
            conditions.append(dataframe['cci-'+str(self.cci_TP.value)] <self.buy_cci_Value.value)
        if self.buy_rsi_enabled.value:
            conditions.append(dataframe['rsi-'+str(self.rsi_TP.value)]<self.buy_rsi_Value.value)
       
        if conditions:
            dataframe.loc[reduce(lambda x,y:x&y,conditions),
            'buy']=1
           
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions=[]
        if self.sell_cci_enabled.value:
            conditions.append(dataframe['cci-'+str(self.cci_TP.value)] >self.sell_cci_Value.value)
        if self.sell_rsi_enabled.value:
            conditions.append(dataframe['rsi-'+str(self.rsi_TP.value)]>self.sell_rsi_Value.value)
       
        if conditions:
            dataframe.loc[reduce(lambda x,y:x&y,conditions),
            'Sell']=1
           
        return dataframe
