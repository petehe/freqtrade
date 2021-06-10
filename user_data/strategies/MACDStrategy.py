
# --- Do not remove these libs ---
from freqtrade.strategy.interface import IStrategy
from typing import Dict, List
from functools import reduce
from pandas import DataFrame
from freqtrade.strategy import IntParameter
# --------------------------------

import talib.abstract as ta


class MACDStrategy(IStrategy):
    """

    author@: Gert Wohlgemuth

    idea:

        uptrend definition:
            MACD above MACD signal
            and CCI < -50

        downtrend definition:
            MACD below MACD signal
            and CCI > 100

    """

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi"
    minimal_roi = {
        "0": 0.26,
        "14": 0.076,
        "30": 0.016,
        "43": 0
    }


    # Optimal stoploss designed for the strategy
    # This attribute will be overridden if the config file contains "stoploss"
    stoploss = -0.026

    # Trailing stop:
    trailing_stop = True
    trailing_stop_positive = 0.024
    trailing_stop_positive_offset = 0.084
    trailing_only_offset_is_reached = True
    
    # Optimal timeframe for the strategy
    timeframe = '5m'

    buy_cci_value=IntParameter(-200,-50,default=-198,space='buy')
    sell_cci_value=IntParameter(50,200,default=120,space='sell')

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        macd = ta.MACD(dataframe)
        dataframe['macd'] = macd['macd']
        dataframe['macdsignal'] = macd['macdsignal']
        dataframe['macdhist'] = macd['macdhist']
        dataframe['cci'] = ta.CCI(dataframe)

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the buy signal for the given dataframe
        :param dataframe: DataFrame
        :return: DataFrame with buy column
        """
        conditions=[]
        conditions.append(dataframe['macd'] > dataframe['macdsignal'])
        conditions.append(dataframe['cci']<=self.buy_cci_value.value)

        if conditions:
            dataframe.loc[reduce(lambda x,y:x&y, conditions),'buy']=1
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the sell signal for the given dataframe
        :param dataframe: DataFrame
        :return: DataFrame with buy column
        """
        conditions=[]
        conditions.append(dataframe['macd'] <dataframe['macdsignal'])
        conditions.append(dataframe['cci']>=self.sell_cci_value.value)

        if conditions:
            dataframe.loc[reduce(lambda x,y:x&y, conditions),'sell']=1
        return dataframe
