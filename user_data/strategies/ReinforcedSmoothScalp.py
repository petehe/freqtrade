# --- Do not remove these libs ---
from freqtrade.strategy.hyper import IntParameter
from freqtrade.strategy.interface import IStrategy
from freqtrade.strategy import timeframe_to_minutes
from pandas import DataFrame
from technical.util import resample_to_interval, resampled_merge
import numpy  # noqa

# --------------------------------
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib


class ReinforcedSmoothScalp(IStrategy):
    """
    this strategy is based around the idea of generating a lot of potentatils buys and make tiny profits on each trade
    we recommend to have at least 60 parallel trades at any time to cover non avoidable losses
    """

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi"
    minimal_roi = {"0": 0.02}
    # Optimal stoploss designed for the strategy
    # This attribute will be overridden if the config file contains "stoploss"
    # should not be below 3% loss

    stoploss = -0.1
    # Optimal timeframe for the strategy
    # the shorter the better
    timeframe = "1m"

    # resample factor to establish our general trend. Basically don't buy if a trend is not given
    resample_factor = 5

    both_ema_period = IntParameter(3, 20, default=5, space="buy")
    both_cci_period = IntParameter(10, 40, default=20, space="buy")

    buy_adx_value = IntParameter(20, 50, default=30, space="buy")
    buy_mfi_value = IntParameter(20, 50, default=30, space="buy")
    buy_fastd_value = IntParameter(20, 50, default=30, space="buy")
    buy_fastk_value = IntParameter(20, 50, default=30, space="buy")
    buy_cci_value = IntParameter(-200, -100, default=-150, space="buy")

    sell_fastd_value = IntParameter(60, 90, default=70, space="sell")
    sell_fastk_value = IntParameter(60, 90, default=70, space="sell")
    sell_cci_value = IntParameter(100, 200, default=150, space="sell")

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        tf_res = timeframe_to_minutes(self.timeframe) * 5
        df_res = resample_to_interval(dataframe, tf_res)
        df_res["sma"] = ta.SMA(df_res, 50, price="close")
        dataframe = resampled_merge(dataframe, df_res, fill_na=True)
        dataframe["resample_sma"] = dataframe[f"resample_{tf_res}_sma"]

        for val in self.both_ema_period.range:
            dataframe[f"ema_high{val}"] = ta.EMA(dataframe, timeperiod=val, price="high")
            dataframe[f"ema_close{val}"] = ta.EMA(dataframe, timeperiod=val, price="close")
            dataframe[f"ema_low{val}"] = ta.EMA(dataframe, timeperiod=val, price="low")
        stoch_fast = ta.STOCHF(dataframe, 5, 3, 0, 3, 0)
        dataframe["fastd"] = stoch_fast["fastd"]
        dataframe["fastk"] = stoch_fast["fastk"]
        dataframe["adx"] = ta.ADX(dataframe)
        for val in self.both_cci_period.range:
            dataframe[f"cci{val}"] = ta.CCI(dataframe, timeperiod=val)
        # dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["mfi"] = ta.MFI(dataframe)

        # required for graphing
        # bollinger = qtpylib.bollinger_bands(dataframe["close"], window=20, stds=2)
        # dataframe["bb_lowerband"] = bollinger["lower"]
        # dataframe["bb_upperband"] = bollinger["upper"]
        # dataframe["bb_middleband"] = bollinger["mid"]

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (
                    (dataframe["open"] < dataframe[f"ema_low{self.both_ema_period.value}"])
                    & (dataframe["adx"] > self.buy_adx_value.value)
                    & (dataframe["mfi"] < self.buy_mfi_value.value)
                    & (
                        (dataframe["fastk"] < self.buy_fastk_value.value)
                        & (dataframe["fastd"] < self.buy_fastd_value.value)
                        & (qtpylib.crossed_above(dataframe["fastk"], dataframe["fastd"]))
                    )
                    & (dataframe["resample_sma"] < dataframe["close"])
                )
                # |
                # # try to get some sure things independent of resample
                # ((dataframe['rsi'] - dataframe['mfi']) < 10) &
                # (dataframe['mfi'] < 30) &
                # (dataframe['cci'] < -200)
            ),
            "buy",
        ] = 1
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (
                    ((dataframe["open"] >= dataframe[f"ema_high{self.both_ema_period.value}"]))
                    | (
                        (qtpylib.crossed_above(dataframe["fastk"], self.sell_fastk_value.value))
                        | (qtpylib.crossed_above(dataframe["fastd"], self.sell_fastd_value.value))
                    )
                )
                & (dataframe[f"cci{self.both_cci_period.value}"] > self.sell_cci_value.value)
            ),
            "sell",
        ] = 1
        return dataframe
