# --- Do not remove these libs ---
from freqtrade.strategy.hyper import IntParameter
from freqtrade.strategy.interface import IStrategy
from typing import Dict, List
from functools import reduce
from pandas import DataFrame, merge, DatetimeIndex

# --------------------------------

import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from technical.util import resample_to_interval, resampled_merge
from freqtrade.exchange import timeframe_to_minutes


class ReinforcedAverageStrategy(IStrategy):
    """

    author@: Gert Wohlgemuth

    idea:
        buys and sells on crossovers - doesn't really perfom that well and its just a proof of concept
    """

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi"
    minimal_roi = {"0": 0.5}

    # Optimal stoploss designed for the strategy
    # This attribute will be overridden if the config file contains "stoploss"
    stoploss = -0.2

    # Optimal timeframe for the strategy
    timeframe = "4h"

    # trailing stoploss
    trailing_stop = False
    trailing_stop_positive = 0.01
    trailing_stop_positive_offset = 0.02
    trailing_only_offset_is_reached = False

    # run "populate_indicators" only for new candle
    process_only_new_candles = False

    # Experimental settings (configuration will overide these if set)
    use_sell_signal = True
    sell_profit_only = False
    ignore_roi_if_buy_signal = False

    both_ma_short_period = IntParameter(3, 15, default=8, space="buy")
    both_ma_medium_period = IntParameter(15, 35, default=21, space="buy")
    both_ma_long_period = IntParameter(30, 70, default=50, space="sell")

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        for val in self.both_ma_short_period.range:
            dataframe[f"maShort{val}"] = ta.EMA(dataframe, timeperiod=val)
        for val in self.both_ma_medium_period.range:
            dataframe[f"maMedium{val}"] = ta.EMA(dataframe, timeperiod=val)
        ##################################################################################
        # required for graphing
        # bollinger = qtpylib.bollinger_bands(dataframe["close"], window=20, stds=2)
        # dataframe["bb_lowerband"] = bollinger["lower"]
        # dataframe["bb_upperband"] = bollinger["upper"]
        # dataframe["bb_middleband"] = bollinger["mid"]
        self.resample_interval = timeframe_to_minutes(self.timeframe) * 12
        dataframe_long = resample_to_interval(dataframe, self.resample_interval)
        for val in self.both_ma_long_period.range:
            dataframe_long[f"malong{val}"] = ta.SMA(dataframe_long, timeperiod=val, price="close")
        dataframe = resampled_merge(dataframe, dataframe_long, fill_na=True)

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the buy signal for the given dataframe
        :param dataframe: DataFrame
        :return: DataFrame with buy column
        """

        dataframe.loc[
            (
                qtpylib.crossed_above(
                    dataframe[f"maShort{self.both_ma_short_period.value}"],
                    dataframe[f"maMedium{self.both_ma_medium_period.value}"],
                )
                & (
                    dataframe["close"]
                    > dataframe[
                        f"resample_{self.resample_interval}_malong{self.both_ma_long_period.value}"
                    ]
                )
                & (dataframe["volume"] > 0)
            ),
            "buy",
        ] = 1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the sell signal for the given dataframe
        :param dataframe: DataFrame
        :return: DataFrame with buy column
        """
        dataframe.loc[
            (
                qtpylib.crossed_above(
                    dataframe[f"maMedium{self.both_ma_medium_period.value}"],
                    dataframe[f"maShort{self.both_ma_short_period.value}"],
                )
                & (dataframe["volume"] > 0)
            ),
            "sell",
        ] = 1
        return dataframe
