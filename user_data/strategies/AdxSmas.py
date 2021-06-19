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
        "0": 0.601,
        "462": 0.168,
        "1099": 0.037,
        "1888": 0
    }


    # Optimal stoploss designed for the strategy
    stoploss =  -0.241
    trailing_stop = True
    trailing_stop_positive = 0.016
    trailing_stop_positive_offset = 0.028
    trailing_only_offset_is_reached = True
    # Optimal timeframe for the strategy
    timeframe = '1h'

    #define hyperopt parameters
    buy_adx=IntParameter(20,40, default=24,space='buy')
    buy_adx_enabled=CategoricalParameter([True,False],default=True,space='buy')
    buy_ema_short=IntParameter(3,50, default=49,space='buy')
    buy_ema_long=IntParameter (15,200,default=189,space='buy')
    sell_ema_short=IntParameter(3,50, default=30,space='sell')
    sell_ema_long=IntParameter (15,200,default=192,space='sell')
    sell_adx=IntParameter(20,40, default=22,space='sell')
    sell_adx_enabled=CategoricalParameter([True,False],default=True,space='sell')
    
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['adx']=ta.ADX(dataframe)
        for val in self.buy_ema_short.range:
            dataframe[f'buy_ema_short_{val}']=ta.EMA(dataframe,val)
        for val in self.buy_ema_long.range:
            dataframe[f'buy_ema_long_{val}']=ta.EMA(dataframe,val)
        
        for val in self.sell_ema_short.range:
            dataframe[f'sell_ema_short_{val}']=ta.EMA(dataframe,val)
        for val in self.sell_ema_long.range:
            dataframe[f'sell_ema_long_{val}']=ta.EMA(dataframe,val)

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                    (dataframe['adx']>self.buy_adx.value if self.buy_adx_enabled.value else True) &
                    qtpylib.crossed_above(dataframe[f'buy_ema_short_{self.buy_ema_short.value}'],dataframe[f'buy_ema_long_{self.buy_ema_long.value}'])
            ),
            'buy'] = 1
        return dataframe


    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                    (dataframe['adx']<self.sell_adx.value if self.sell_adx_enabled.value else True) &
                    (qtpylib.crossed_below(dataframe[f'sell_ema_short_{self.sell_ema_short.value}'],dataframe[f'sell_ema_long_{self.sell_ema_long.value}']))
            ),
            'sell'] = 1

        


        return dataframe

