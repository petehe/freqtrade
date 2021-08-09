# --- Do not remove these libs ---
from freqtrade.strategy.hyper import IntParameter
from freqtrade.strategy.interface import IStrategy
from typing import Dict, List
from functools import reduce
from pandas import DataFrame

# --------------------------------
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from typing import Dict, List
from functools import reduce
from pandas import DataFrame, DatetimeIndex, merge

# --------------------------------
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
import numpy  # noqa


class SmoothScalp(IStrategy):
    """
    this strategy is based around the idea of generating a lot of potentatils buys and make tiny profits on each trade

    we recommend to have at least 60 parallel trades at any time to cover non avoidable losses
    """

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi"
    minimal_roi = {"0": 0.01}
    # Optimal stoploss designed for the strategy
    # This attribute will be overridden if the config file contains "stoploss"
    # should not be below 3% loss

    stoploss = -0.5
    # Optimal timeframe for the strategy
    # the shorter the better
    timeframe = "1m"

    both_ema_period = IntParameter(3, 10, default=5, space="buy")
    both_cci_period = IntParameter(10, 30, default=20, space="buy")
    both_rsi_period = IntParameter(7, 21, default=14, space="buy")

    buy_adx_value = IntParameter(20, 40, default=30, space="buy")
    buy_mfi_value = IntParameter(20, 40, default=30, space="buy")
    buy_fastd_value = IntParameter(20, 40, default=30, space="buy")
    buy_fastk_value = IntParameter(20, 40, default=30, space="buy")
    buy_cci_value = IntParameter(-200, -100, default=-150, space="buy")

    sell_fastd_value = IntParameter(60, 90, default=70, space="sell")
    sell_fastk_value = IntParameter(60, 90, default=70, space="sell")
    sell_cci_value = IntParameter(100, 200, default=150, space="sell")

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        for val in self.both_ema_period.range:
            dataframe[f"ema_high{val}"] = ta.EMA(dataframe, timeperiod=val, price="high")
            dataframe[f"ema_close{val}"] = ta.EMA(dataframe, timeperiod=5, price="close")
            dataframe[f"ema_low{val}"] = ta.EMA(dataframe, timeperiod=5, price="low")
        stoch_fast = ta.STOCHF(dataframe, 5, 3, 0, 3, 0)
        dataframe["fastd"] = stoch_fast["fastd"]
        dataframe["fastk"] = stoch_fast["fastk"]
        dataframe["adx"] = ta.ADX(dataframe)
        for val in self.both_cci_period.range:
            dataframe[f"cci{val}"] = ta.CCI(dataframe, timeperiod=val)
        dataframe["mfi"] = ta.MFI(dataframe)

        # required for graphing
        # bollinger = qtpylib.bollinger_bands(dataframe["close"], window=20, stds=2)
        # dataframe["bb_lowerband"] = bollinger["lower"]
        # dataframe["bb_upperband"] = bollinger["upper"]
        # dataframe["bb_middleband"] = bollinger["mid"]
        # macd = ta.MACD(dataframe)
        # dataframe["macd"] = macd["macd"]
        # dataframe["macdsignal"] = macd["macdsignal"]
        # dataframe["macdhist"] = macd["macdhist"]
        # dataframe["cci"] = ta.CCI(dataframe)

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
                    & (dataframe[f"cci{self.both_cci_period.value}"] < self.buy_cci_value.value)
                )
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
