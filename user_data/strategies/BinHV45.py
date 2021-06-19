# --- Do not remove these libs ---
from freqtrade.strategy.hyper import IntParameter
from freqtrade.strategy.interface import IStrategy
from typing import Dict, List
from functools import reduce
from pandas import DataFrame
import numpy as np
# --------------------------------

import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib


def bollinger_bands(stock_price, window_size, num_of_std):
    rolling_mean = stock_price.rolling(window=window_size).mean()
    rolling_std = stock_price.rolling(window=window_size).std()
    lower_band = rolling_mean - (rolling_std * num_of_std)

    return rolling_mean, lower_band


class BinHV45(IStrategy):
    minimal_roi = {
        "0": 0.0125
    }

    stoploss = -0.05
    timeframe = '1m'

    bb_std=IntParameter(1,3,default=2,space='all')

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        for val in self.bb_std.range:
            mid, lower = bollinger_bands(dataframe['close'], window_size=40, num_of_std=val)
            dataframe[f'mid{val}'] = np.nan_to_num(mid)
            dataframe[f'lower{val}'] = np.nan_to_num(lower)
            dataframe[f'bbdelta{val}'] = (dataframe[f'mid{val}'] - dataframe[f'lower{val}']).abs()
        dataframe['pricedelta'] = (dataframe['open'] - dataframe['close']).abs()
        dataframe['closedelta'] = (dataframe['close'] - dataframe['close'].shift()).abs()
        dataframe['tail'] = (dataframe['close'] - dataframe['low']).abs()
        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # dataframe.loc[
        #     (
        #         dataframe['lower'].shift().gt(0) &
        #         dataframe['bbdelta'].gt(dataframe['close'] * 0.008) &
        #         dataframe['closedelta'].gt(dataframe['close'] * 0.0175) &
        #         dataframe['tail'].lt(dataframe['bbdelta'] * 0.25) &
        #         dataframe['close'].lt(dataframe['lower'].shift()) &
        #         dataframe['close'].le(dataframe['close'].shift())
        #     ),
        #     'buy'] = 1
        dataframe.loc[
            (
                dataframe[f'lower{self.bb_std.value}'].shift().gt(0) &
                dataframe[f'bbdelta{self.bb_std.value}'].gt(dataframe['close'] * 0.008) &
                dataframe['closedelta'].gt(dataframe['close'] * 0.0175) &
                dataframe['tail'].lt(dataframe[f'bbdelta{self.bb_std.value}'] * 0.25) &
                dataframe['close'].lt(dataframe[f'lower{self.bb_std.value}'].shift()) &
                dataframe['close'].le(dataframe['close'].shift())
            ),
            'buy'] = 1        
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        no sell signal
        """
        dataframe.loc[:, 'sell'] = 0
        return dataframe
