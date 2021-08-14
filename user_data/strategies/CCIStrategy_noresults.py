# --- Do not remove these libs ---
from freqtrade.strategy.hyper import DecimalParameter, IntParameter
from freqtrade.strategy.interface import IStrategy
from typing import Dict, List
from functools import reduce
from pandas import DataFrame, Series, DatetimeIndex, merge

# --------------------------------

import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib

# hyperopt doesn't produce any results
class CCIStrategy(IStrategy):
    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi"
    minimal_roi = {"0": 0.1}

    # Optimal stoploss designed for the strategy
    # This attribute will be overridden if the config file contains "stoploss"
    stoploss = -0.02

    # Optimal timeframe for the strategy
    timeframe = "1m"

    cci_one_tp = IntParameter(150, 200, default=170, space="buy")
    cci_two_tp = IntParameter(18, 52, default=34, space="buy")
    buy_cci_one_value = IntParameter(-150, -50, default=-100, space="buy")
    buy_cci_two_value = IntParameter(-150, -50, default=-100, space="buy")
    buy_cmf_value = DecimalParameter(-0.25, -0.01, default=-0.1, space="buy")
    buy_mfi_value = IntParameter(10, 50, default=25, space="buy")

    sell_cci_one_value = IntParameter(50, 200, default=100, space="sell")
    sell_cci_two_value = IntParameter(50, 200, default=100, space="sell")
    sell_cmf_value = DecimalParameter(0.1, 0.5, default=0.3, space="sell")

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe = self.resample(dataframe, self.timeframe, 5)
        dataframe["cci_one"] = ta.CCI(dataframe, timeperiod=170)
        dataframe["cci_two"] = ta.CCI(dataframe, timeperiod=34)
        dataframe["rsi"] = ta.RSI(dataframe)
        dataframe["mfi"] = ta.MFI(dataframe)

        dataframe["cmf"] = self.chaikin_mf(dataframe)

        # # required for graphing
        # bollinger = qtpylib.bollinger_bands(dataframe["close"], window=20, stds=2)
        # dataframe["bb_lowerband"] = bollinger["lower"]
        # dataframe["bb_upperband"] = bollinger["upper"]
        # dataframe["bb_middleband"] = bollinger["mid"]

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the buy signal for the given dataframe
        :param dataframe: DataFrame
        :return: DataFrame with buy column
        """
        dataframe.loc[
            (
                (dataframe["cci_one"] < self.buy_cci_one_value.value)
                & (dataframe["cci_two"] < self.buy_cci_two_value.value)
                & (dataframe["cmf"] < self.buy_cmf_value.value)
                & (dataframe["mfi"] < self.buy_mfi_value.value)
                # insurance
                & (dataframe["resample_medium"] > dataframe["resample_short"])
                & (dataframe["resample_long"] < dataframe["close"])
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
                (dataframe["cci_one"] > self.sell_cci_one_value.value)
                & (dataframe["cci_two"] > self.sell_cci_two_value.value)
                & (dataframe["cmf"] > self.sell_cmf_value.value)
                & (dataframe["resample_sma"] < dataframe["resample_medium"])
                & (dataframe["resample_medium"] < dataframe["resample_short"])
            ),
            "sell",
        ] = 1
        return dataframe

    def chaikin_mf(self, df, periods=20):
        close = df["close"]
        low = df["low"]
        high = df["high"]
        volume = df["volume"]

        mfv = ((close - low) - (high - close)) / (high - low)
        mfv = mfv.fillna(0.0)  # float division by zero
        mfv *= volume
        cmf = mfv.rolling(periods).sum() / volume.rolling(periods).sum()

        return Series(cmf, name="cmf")

    def resample(self, dataframe, interval, factor):
        # defines the reinforcement logic
        # resampled dataframe to establish if we are in an uptrend, downtrend or sideways trend
        df = dataframe.copy()
        df = df.set_index(DatetimeIndex(df["date"]))
        ohlc_dict = {"open": "first", "high": "max", "low": "min", "close": "last"}
        df = df.resample(str(int(interval[:-1]) * factor) + "min", label="right").agg(ohlc_dict)
        df["resample_sma"] = ta.SMA(df, timeperiod=100, price="close")
        df["resample_medium"] = ta.SMA(df, timeperiod=50, price="close")
        df["resample_short"] = ta.SMA(df, timeperiod=25, price="close")
        df["resample_long"] = ta.SMA(df, timeperiod=200, price="close")
        df = df.drop(columns=["open", "high", "low", "close"])
        df = df.resample(interval[:-1] + "min")
        df = df.interpolate(method="time")
        df["date"] = df.index
        df.index = range(len(df))
        dataframe = merge(dataframe, df, on="date", how="left")
        return dataframe
