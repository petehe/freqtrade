# --- Do not remove these libs ---
from skopt import space
from freqtrade.strategy.hyper import CategoricalParameter
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from freqtrade.strategy import DecimalParameter,IntParameter, CategoricalParameter
from functools import reduce

# --------------------------------


class AdxSmas(IStrategy):
    """

    author@: Gert Wohlgemuth

    converted from:

    https://github.com/sthewissen/Mynt/blob/master/src/Mynt.Core/Strategies/AdxSmas.cs

    """

    # Minimal ROI designed for the strategy.
    # adjust based on market conditions. We would recommend to keep it low for quick turn arounds
    # This attribute will be overridden if the config file contains "minimal_roi"
    minimal_roi = {
        "0": 0.1
    }

    # Optimal stoploss designed for the strategy
    stoploss = -0.25

    # Optimal timeframe for the strategy
    timeframe = '1h'

    #define hyperopt parameters
    buy_adx=IntParameter(20,40, default=30,space='buy')
    buy_adx_enabled=CategoricalParameter([True,False],default=True,space='buy')
    ema_short=IntParameter(10,30, default=20,space='buy,sell')
    ema_long=IntParameter (30,100,default=50,space='buy,sell')
    sell_adx=IntParameter(20,40, default=30,space='sell')
    sell_adx_enabled=CategoricalParameter([True,False],default=True,space='sell')
    
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['adx']=ta.ADX(dataframe)
        for val in self.ema_short.range:
            dataframe[f'ema_short_{val}']=ta.EMA(dataframe,val)
        for val in self.ema_long.range:
            dataframe[f'ema_long_{val}']=ta.EMA(dataframe,val)

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions=[]
        conditions.append(qtpylib.crossed_above(dataframe[f'ema_short_{self.ema_short.value}'],dataframe[f'ema_long_{self.ema_long.value}']))
        if self.buy_adx_enabled.value:
            conditions.append(dataframe['adx']>self.buy_adx.value)
        
        if conditions:
            dataframe.loc[reduce(lambda x,y:x&y,conditions),
            'buy']=1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions=[]
        conditions.append(qtpylib.crossed_below(dataframe[f'ema_short_{self.ema_short.value}'],dataframe[f'ema_long_{self.ema_long.value}']))
        if self.sell_adx_enabled.value:
            conditions.append(dataframe['adx']<self.sell_adx.value)
        
        if conditions:
            dataframe.loc[reduce(lambda x,y:x&y,conditions),
            'sell']=1

        return dataframe

