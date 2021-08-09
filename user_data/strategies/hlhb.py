# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement

from freqtrade.strategy.hyper import IntParameter
import numpy as np  # noqa
import pandas as pd  # noqa
from pandas import DataFrame
from freqtrade.strategy import IStrategy
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib


class hlhb(IStrategy):
    """
    The HLHB ("Huck loves her bucks!") System simply aims to catch short-term forex trends.
    More information in https://www.babypips.com/trading/forex-hlhb-system-explained
    """

    INTERFACE_VERSION = 2

    position_stacking = "True"

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi".
    minimal_roi = {"0": 0.6225, "703": 0.2187, "2849": 0.0363, "5520": 0}

    # Optimal stoploss designed for the strategy.
    # This attribute will be overridden if the config file contains "stoploss".
    stoploss = -0.3211

    # Trailing stoploss
    trailing_stop = True
    trailing_stop_positive = 0.0117
    trailing_stop_positive_offset = 0.0186
    trailing_only_offset_is_reached = True

    # Optimal timeframe for the strategy.
    timeframe = "4h"

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = True

    # These values can be overridden in the "ask_strategy" section in the config.
    use_sell_signal = True
    sell_profit_only = False
    ignore_roi_if_buy_signal = True

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 30

    # Optional order type mapping.
    order_types = {
        "buy": "limit",
        "sell": "limit",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }

    # Optional order time in force.
    order_time_in_force = {"buy": "gtc", "sell": "gtc"}

    plot_config = {
        # Main plot indicators (Moving averages, ...)
        "main_plot": {
            "ema5": {},
            "ema10": {},
        },
        "subplots": {
            # Subplots - each dict defines one additional plot
            "RSI": {
                "rsi": {"color": "red"},
            },
            "ADX": {
                "adx": {},
            },
        },
    }

    both_ema_short = IntParameter(3, 8, default=5, space="buy")
    both_ema_long = IntParameter(8, 15, default=10, space="buy")
    both_rsi_period = IntParameter(5, 20, default=10, space="buy")
    buy_rsi_value = IntParameter(35, 65, default=50, space="buy")
    buy_adx_value = IntParameter(10, 40, default=25, space="buy")
    sell_rsi_value = IntParameter(35, 65, default=50, space="sell")
    sell_adx_value = IntParameter(10, 40, default=25, space="sell")

    def informative_pairs(self):
        return []

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["hl2"] = (dataframe["close"] + dataframe["open"]) / 2

        # Momentum Indicators
        # ------------------------------------

        # RSI
        for val in self.both_rsi_period.range:
            dataframe[f"rsi{val}"] = ta.RSI(dataframe, timeperiod=val, price="hl2")

        # # EMA - Exponential Moving Average
        for val in self.both_ema_short.range:
            dataframe[f"ema_short{val}"] = ta.EMA(dataframe, timeperiod=val)
        for val in self.both_ema_long.range:
            dataframe[f"ema_long{val}"] = ta.EMA(dataframe, timeperiod=val)

        # ADX
        dataframe["adx"] = ta.ADX(dataframe)

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (
                    qtpylib.crossed_above(
                        dataframe[f"rsi{self.both_rsi_period.value}"], self.buy_rsi_value.value
                    )
                )
                & (
                    qtpylib.crossed_above(
                        dataframe[f"ema_short{self.both_ema_short.value}"],
                        dataframe[f"ema_long{self.both_ema_long.value}"],
                    )
                )
                & (dataframe["adx"] > self.buy_adx_value.value)
                & (dataframe["volume"] > 0)  # Make sure Volume is not 0
            ),
            "buy",
        ] = 1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (
                    qtpylib.crossed_below(
                        dataframe[f"rsi{self.both_rsi_period.value}"], self.sell_rsi_value.value
                    )
                )
                & (
                    qtpylib.crossed_below(
                        dataframe[f"ema_short{self.both_ema_short.value}"],
                        dataframe[f"ema_long{self.both_ema_long.value}"],
                    )
                )
                & (dataframe["adx"] > self.sell_adx_value.value)
                & (dataframe["volume"] > 0)  # Make sure Volume is not 0
            ),
            "sell",
        ] = 1
        return dataframe
