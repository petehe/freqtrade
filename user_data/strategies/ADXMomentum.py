# --- Do not remove these libs ---
from freqtrade.strategy.hyper import CategoricalParameter, IntParameter
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame
import talib.abstract as ta
from functools import reduce

# --------------------------------


class ADXMomentum(IStrategy):
    """

    author@: Gert Wohlgemuth

    converted from:

        https://github.com/sthewissen/Mynt/blob/master/src/Mynt.Core/Strategies/AdxMomentum.cs

    """

    # Minimal ROI designed for the strategy.
    # adjust based on market conditions. We would recommend to keep it low for quick turn arounds
    # This attribute will be overridden if the config file contains "minimal_roi"
    minimal_roi = {
        "0": 0.383,
        "288": 0.163,
        "623": 0.085,
        "1604": 0
    }

    # Optimal stoploss designed for the strategy
    # Stoploss:
    stoploss = -0.292

    # Trailing stop:
    trailing_stop = True
    trailing_stop_positive = 0.01
    trailing_stop_positive_offset = 0.053
    trailing_only_offset_is_reached = True
    
    # Optimal timeframe for the strategy
    timeframe = '1h'

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 20

    buy_adx_value=IntParameter(10,50,default=39,space='buy')
    buy_plus_di_value=IntParameter(10,50,default=34,space='buy')
    buy_adx_enabled=CategoricalParameter([True,False],default=False, space='buy')
    buy_di_enabled=CategoricalParameter([True,False],default=True, space='buy')
    buy_mom_enabled=CategoricalParameter([True,False],default=False, space='buy')

    sell_adx_value=IntParameter(10,50,default=18,space='sell')
    sell_minus_di_value=IntParameter(10,50,default=43,space='sell')
    sell_adx_enabled=CategoricalParameter([True,False],default=True, space='sell')
    sell_di_enabled=CategoricalParameter([True,False],default=False, space='sell')
    sell_mom_enabled=CategoricalParameter([True,False],default=True, space='sell')


    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['adx'] = ta.ADX(dataframe, timeperiod=14)
        dataframe['plus_di'] = ta.PLUS_DI(dataframe, timeperiod=25)
        dataframe['minus_di'] = ta.MINUS_DI(dataframe, timeperiod=25)
        dataframe['mom'] = ta.MOM(dataframe, timeperiod=14)

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions=[]
        if self.buy_adx_enabled.value:
            conditions.append(dataframe['adx']>self.buy_adx_value.value)
        if self.buy_di_enabled.value:
            conditions.append(dataframe['plus_di']>self.buy_plus_di_value.value)
            conditions.append(dataframe['plus_di'] > dataframe['minus_di'])
        if self.buy_mom_enabled.value:
            conditions.append(dataframe['mom']>0)

        if conditions:
            dataframe.loc[reduce(lambda x,y:x&y,conditions),
            'buy']=1
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions=[]
        if self.sell_adx_enabled.value:
            conditions.append(dataframe['adx']>self.sell_adx_value.value)
        if self.sell_di_enabled.value:
            conditions.append(dataframe['minus_di']>self.sell_minus_di_value.value)
            conditions.append(dataframe['plus_di'] < dataframe['minus_di'])
        if self.sell_mom_enabled.value:
            conditions.append(dataframe['mom']<0)

        if conditions:
            dataframe.loc[reduce(lambda x,y:x&y,conditions),
            'sell']=1
        return dataframe
