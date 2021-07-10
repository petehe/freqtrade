# --- Do not remove these libs ---
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame
# --------------------------------

import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from freqtrade.strategy import IntParameter

class ema_trend_following(IStrategy):
    """
    author@: Gert Wohlgemuth
    idea:
        buys and sells on crossovers - doesn't really perfom that well and its just a proof of concept
    """

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi"
    minimal_roi = {
        "0": 0.5
    }

    # Optimal stoploss designed for the strategy
    # This attribute will be overridden if the config file contains "stoploss"
    stoploss = -0.2

    # Optimal timeframe for the strategy
    timeframe = '4h'

    ema_short=IntParameter(3,20,default=8,space='buy')
    ema_long=IntParameter(21,100,default=21,space='sell')


    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        for val in self.ema_short.range:
            dataframe[f'ema_s{val}'] = ta.EMA(dataframe, timeperiod=val)
        for val in self.ema_long.range:
            dataframe[f'ema_l{val}'] = ta.EMA(dataframe, timeperiod=val)

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the buy signal for the given dataframe
        :param dataframe: DataFrame
        :return: DataFrame with buy column
        """
        dataframe.loc[
            (
                qtpylib.crossed_above(dataframe[f'ema_s{self.ema_short.value}'], dataframe[f'ema_l{self.ema_long.value}'])
            ),
            'buy'] = 1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the sell signal for the given dataframe
        :param dataframe: DataFrame
        :return: DataFrame with buy column
        """
        dataframe.loc[
            (
                qtpylib.crossed_above(dataframe[f'ema_l{self.ema_long.value}'], dataframe[f'ema_s{self.ema_short.value}'])
            ),
            'sell'] = 1
        return dataframe