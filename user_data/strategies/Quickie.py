# --- Do not remove these libs ---
from freqtrade.strategy.interface import IStrategy
from typing import Dict, List
from functools import reduce
from pandas import DataFrame

# --------------------------------

import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from freqtrade.strategy.hyper import CategoricalParameter, IntParameter
from functools import reduce


class Quickie(IStrategy):
    """

    author@: Gert Wohlgemuth

    idea:
        momentum based strategie. The main idea is that it closes trades very quickly, while avoiding excessive losses. Hence a rather moderate stop loss in this case
    """

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi"
    minimal_roi = {
        "100": 0.01,
        "30": 0.03,
        "15": 0.06,
        "10": 0.15,
    }

    # Optimal stoploss designed for the strategy
    # This attribute will be overridden if the config file contains "stoploss"
    stoploss = -0.25

    # Optimal timeframe for the strategy
    timeframe = "5m"

    buy_bbband = CategoricalParameter(["upper", "lower", "mid"], default="lower", space="buy")
    sell_bbband = CategoricalParameter(["upper", "lower", "mid"], default="lower", space="sell")
    buy_bbstd = IntParameter(1, 4, default=2, space="buy")
    sell_bbstd = IntParameter(1, 4, default=2, space="sell")
    buy_adx_value = IntParameter(20, 100, default=30, space="buy")
    sell_adx_value = IntParameter(20, 100, default=70, space="sell")
    tema_value = IntParameter(5, 20, default=9, space="buy")
    sma_value = IntParameter(100, 300, default=200, space="buy")

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # macd = ta.MACD(dataframe)
        # dataframe['macd'] = macd['macd']
        # dataframe['macdsignal'] = macd['macdsignal']
        # dataframe['macdhist'] = macd['macdhist']
        for val in self.tema_value.range:
            dataframe[f"tema{val}"] = ta.TEMA(dataframe, timeperiod=val)
        for val in self.sma_value.range:
            dataframe[f"sma{val}"] = ta.SMA(dataframe, timeperiod=val)
        # dataframe['sma_50'] = ta.SMA(dataframe, timeperiod=50)

        dataframe["adx"] = ta.ADX(dataframe)

        # required for graphing

        for std in self.buy_bbstd.range:
            bollinger = qtpylib.bollinger_bands(
                qtpylib.typical_price(dataframe), window=20, stds=std
            )
            for band in self.buy_bbband.opt_range:
                dataframe[f"buybb_{band}band{std}"] = bollinger[band]

        for std in self.sell_bbstd.range:
            bollinger = qtpylib.bollinger_bands(
                qtpylib.typical_price(dataframe), window=20, stds=std
            )
            for band in self.buy_bbband.opt_range:
                dataframe[f"sellbb_{band}band{std}"] = bollinger[band]

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = []
        conditions.append(dataframe["adx"] > self.buy_adx_value.value)
        conditions.append(
            dataframe[f"tema{self.tema_value.value}"]
            < dataframe[f"buybb_{self.buy_bbband.value}band{self.buy_bbstd.value}"]
        )
        conditions.append(
            dataframe[f"tema{self.tema_value.value}"]
            > dataframe[f"tema{self.tema_value.value}"].shift(1)
        )
        conditions.append(dataframe[f"sma{self.sma_value.value}"] > dataframe["close"])
        if conditions:
            dataframe.loc[reduce(lambda x, y: x & y, conditions), "buy"] = 1
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = []
        conditions.append(dataframe["adx"] > self.sell_adx_value.value)
        conditions.append(
            dataframe[f"tema{self.tema_value.value}"]
            > dataframe[f"sellbb_{self.buy_bbband.value}band{self.sell_bbstd.value}"]
        )
        conditions.append(
            dataframe[f"tema{self.tema_value.value}"]
            < dataframe[f"tema{self.tema_value.value}"].shift(1)
        )

        if conditions:
            dataframe.loc[reduce(lambda x, y: x & y, conditions), "sell"] = 1

        return dataframe
