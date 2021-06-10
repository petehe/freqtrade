# --- Do not remove these libs ---
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from freqtrade.strategy import CategoricalParameter
from functools import reduce
# --------------------------------


class AwesomeMacd(IStrategy):
    """

    author@: Gert Wohlgemuth

    converted from:

    https://github.com/sthewissen/Mynt/blob/master/src/Mynt.Core/Strategies/AwesomeMacd.cs

    """

    # Minimal ROI designed for the strategy.
    # adjust based on market conditions. We would recommend to keep it low for quick turn arounds
    # This attribute will be overridden if the config file contains "minimal_roi"
    minimal_roi = {
        "0": 0.334,
        "288": 0.144,
        "456": 0.091,
        "1406": 0
    }

    # Optimal stoploss designed for the strategy
    # Stoploss:
    stoploss = -0.221

    # Trailing stop:
    trailing_stop = True
    trailing_stop_positive = 0.013
    trailing_stop_positive_offset = 0.108
    trailing_only_offset_is_reached = False

    # Optimal timeframe for the strategy
    timeframe = '1h'
    buy_ao_enabled=CategoricalParameter([True,False],default=True,space='buy')
    sell_ao_enabled=CategoricalParameter([True,False], default=False, space='sell')
    buy_macd_enabled=CategoricalParameter([True,False],default=False,space='buy')
    sell_macd_enabled=CategoricalParameter([True,False], default=True, space='sell')
    buy_macdsingal_enabled=CategoricalParameter([True,False],default=True,space='buy')
    sell_macdsingal_enabled=CategoricalParameter([True,False], default=True, space='sell')

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['ao'] = qtpylib.awesome_oscillator(dataframe)

        macd = ta.MACD(dataframe)
        dataframe['macd'] = macd['macd']
        dataframe['macdsignal'] = macd['macdsignal']
        dataframe['macdhist'] = macd['macdhist']

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions=[]
        if self.buy_ao_enabled:
            conditions.append((dataframe['ao'] > 0) & (dataframe['ao'].shift() < 0))
        if self.buy_macd_enabled:
            conditions.append(dataframe['macd']>0)
        if self.buy_macdsingal_enabled:
            conditions.append(dataframe['macd']>dataframe['macdsignal'])
        if conditions:
            dataframe.loc[reduce(lambda x,y: x&y,conditions),'buy']=1
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions=[]
        if self.sell_ao_enabled:
            conditions.append((dataframe['ao'] < 0) & (dataframe['ao'].shift() > 0))
        if self.sell_macd_enabled:
            conditions.append(dataframe['macd']<0)
        if self.sell_macdsingal_enabled:
            conditions.append(dataframe['macd']<dataframe['macdsignal'])
        if conditions:
            dataframe.loc[reduce(lambda x,y: x&y,conditions),'sell']=1
        return dataframe
