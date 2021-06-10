from skopt import space
from freqtrade.strategy.hyper import CategoricalParameter
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from freqtrade.strategy import DecimalParameter,IntParameter, CategoricalParameter
from functools import reduce


class DoesNothingStrategy(IStrategy):
    
    # Minimal ROI designed for the strategy.
    # adjust based on market conditions. We would recommend to keep it low for quick turn arounds
    # This attribute will be overridden if the config file contains "minimal_roi"
    minimal_roi = {
        "0": 10
    }


    # Optimal stoploss designed for the strategy
    stoploss =  -0.241

    # Optimal timeframe for the strategy
    timeframe = '1h'

    #define hyperopt parameters
    badx=IntParameter(20,40, default=24,space='buy')
    sadx=IntParameter(20,40, default=22,space='sell')
    
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['adx']=ta.ADX(dataframe)

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions=[]
        conditions.append(dataframe['adx']>self.badx.value)
        
        if conditions:
            dataframe.loc[reduce(lambda x,y:x&y,conditions),
            'buy']=1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions=[]
        conditions.append(dataframe['adx']<self.sadx.value)
        
        if conditions:
            dataframe.loc[reduce(lambda x,y:x&y,conditions),
            'sell']=1

        return dataframe