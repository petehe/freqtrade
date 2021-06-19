from freqtrade.strategy.hyper import IntParameter
from freqtrade.strategy.interface import IStrategy
from typing import Dict, List
from functools import reduce
from pandas import DataFrame
# --------------------------------

import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
import numpy  # noqa


class EMASkipPump(IStrategy):

    """
        basic strategy, which trys to avoid pump and dump market conditions. Shared from the tradingview
        slack
    """

    # Minimal ROI designed for the strategy.
    # we only sell after 100%, unless our sell points are found before
    minimal_roi = {
        "0": 0.1
    }

    # Optimal stoploss designed for the strategy
    # This attribute will be overridden if the config file contains "stoploss"
    # should be converted to a trailing stop loss
    stoploss = -0.05

    # Optimal timeframe for the strategy
    timeframe = '5m'

    # EMA_SHORT_TERM = 5
    # EMA_MEDIUM_TERM = 12
    # EMA_LONG_TERM = 21

    EMA_SHORT_TERM =IntParameter(3,9,default=5,space='buy')
    EMA_MEDIUM_TERM=IntParameter(10,17,default=12,space='buy')
    EMA_LONG_TERM=IntParameter(18,30,default=21,space='buy')
    bb_std=IntParameter(1,3,default=2,space='sell')
    buy_volume_window=IntParameter(20,40,default=30,space='buy')
    buy_volume_multi=IntParameter(10,30,default=20,space='buy')

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """ Adds several different TA indicators to the given DataFrame
        """
        for val in self.EMA_SHORT_TERM.range:
            dataframe[f'ema_short{val}']=ta.EMA(dataframe,timeperiod=val)
        for val in self.EMA_MEDIUM_TERM.range:
            dataframe[f'ema_medium{val}']=ta.EMA(dataframe,timeperiod=val)
            dataframe[f'min{val}'] = ta.MIN(dataframe, timeperiod=val)
            dataframe[f'max{val}'] = ta.MAX(dataframe, timeperiod=val)
        for val in self.EMA_LONG_TERM.range:
            dataframe[f'ema_long{val}']=ta.EMA(dataframe,timeperiod=val)
        for val in self.bb_std.range:
            bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=val)
            dataframe[f'bb_lower{val}'] = bollinger['lower']
            dataframe[f'bb_mid{val}'] = bollinger['mid']
            dataframe[f'bb_upper{val}'] = bollinger['upper']

        # dataframe['ema_{}'.format(self.EMA_SHORT_TERM)] = ta.EMA(
        #     dataframe, timeperiod=self.EMA_SHORT_TERM
        # )
        # dataframe['ema_{}'.format(self.EMA_MEDIUM_TERM)] = ta.EMA(
        #     dataframe, timeperiod=self.EMA_MEDIUM_TERM
        # )
        # dataframe['ema_{}'.format(self.EMA_LONG_TERM)] = ta.EMA(
        #     dataframe, timeperiod=self.EMA_LONG_TERM
        # )

        # bollinger = qtpylib.bollinger_bands(
        #     qtpylib.typical_price(dataframe), window=20, stds=2
        # )
        # dataframe['bb_lowerband'] = bollinger['lower']
        # dataframe['bb_middleband'] = bollinger['mid']
        # dataframe['bb_upperband'] = bollinger['upper']

        # dataframe['min'] = ta.MIN(dataframe, timeperiod=self.EMA_MEDIUM_TERM)
        # dataframe['max'] = ta.MAX(dataframe, timeperiod=self.EMA_MEDIUM_TERM)

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe['volume'] < (dataframe['volume'].rolling(window=self.buy_volume_window.value).mean().shift(1) * self.buy_volume_multi.value)) &
            (dataframe['close'] < dataframe[f'ema_short{self.EMA_SHORT_TERM.value}']) &
            (dataframe['close'] < dataframe[f'ema_medium{self.EMA_MEDIUM_TERM.value}']) &
            (dataframe['close'] == dataframe[f'min{self.EMA_MEDIUM_TERM.value}']) &
            (dataframe['close'] <= dataframe[f'bb_lower{self.bb_std.value}']),
            'buy'
        ] = 1

        # dataframe.loc[
        #     (dataframe['volume'] < (dataframe['volume'].rolling(window=30).mean().shift(1) * 20)) &
        #     (dataframe['close'] < dataframe['ema_{}'.format(self.EMA_SHORT_TERM)]) &
        #     (dataframe['close'] < dataframe['ema_{}'.format(self.EMA_MEDIUM_TERM)]) &
        #     (dataframe['close'] == dataframe['min']) &
        #     (dataframe['close'] <= dataframe['bb_lowerband']),
        #     'buy'
        # ] = 1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        # dataframe.loc[
        #     (dataframe['close'] > dataframe['ema_{}'.format(self.EMA_SHORT_TERM)]) &
        #     (dataframe['close'] > dataframe['ema_{}'.format(self.EMA_MEDIUM_TERM)]) &
        #     (dataframe['close'] >= dataframe['max']) &
        #     (dataframe['close'] >= dataframe['bb_upperband']),
        #     'sell'
        # ] = 1
        dataframe.loc[
            (dataframe['close'] > dataframe[f'ema_short{self.EMA_SHORT_TERM.value}']) &
            (dataframe['close'] > dataframe[f'ema_medium{self.EMA_MEDIUM_TERM.value}']) &
            (dataframe['close'] >= dataframe[f'max{self.EMA_MEDIUM_TERM.value}']) &
            (dataframe['close'] >= dataframe[f'bb_upper{self.bb_std.value}']),
            'sell'
        ] = 1
        return dataframe
