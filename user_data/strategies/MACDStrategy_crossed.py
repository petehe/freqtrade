
# --- Do not remove these libs ---
from freqtrade.strategy.interface import IStrategy
from typing import Dict, List
from functools import reduce
from pandas import DataFrame
# --------------------------------

import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from freqtrade.strategy import IntParameter


class MACDStrategy_crossed(IStrategy):
    """
        buy:
            MACD crosses MACD signal above
            and CCI < -50
        sell:
            MACD crosses MACD signal below
            and CCI > 100
    """

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi"
    minimal_roi = {
        "60":  0.01,
        "30":  0.03,
        "20":  0.04,
        "0":  0.05
    }

    # Optimal stoploss designed for the strategy
    # This attribute will be overridden if the config file contains "stoploss"
    stoploss = -0.3

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
        conditions.append(qtpylib.crossed_above(dataframe['macd'], dataframe['macdsignal']))
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
        conditions.append(qtpylib.crossed_below(dataframe['macd'], dataframe['macdsignal']))
        conditions.append(dataframe['cci']>=self.sell_cci_value.value)

        if conditions:
            dataframe.loc[reduce(lambda x,y:x&y, conditions),'sell']=1
        return dataframe        

