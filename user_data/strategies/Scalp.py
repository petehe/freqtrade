# --- Do not remove these libs ---
from freqtrade.strategy.hyper import IntParameter
from freqtrade.strategy.interface import IStrategy
from typing import Dict, List
from functools import reduce
from pandas import DataFrame
# --------------------------------
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
# --------------------------------
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib


class Scalp(IStrategy):
    """
        this strategy is based around the idea of generating a lot of potentatils buys and make tiny profits on each trade

        we recommend to have at least 60 parallel trades at any time to cover non avoidable losses.

        Recommended is to only sell based on ROI for this strategy
    """

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi"
    minimal_roi = {
        "0": 0.01
    }
    # Optimal stoploss designed for the strategy
    # This attribute will be overridden if the config file contains "stoploss"
    # should not be below 3% loss

    stoploss = -0.04
    # Optimal timeframe for the strategy
    # the shorter the better
    timeframe = '1m'

    ema_tp=IntParameter(3,20,default=5,space='buy')
    buy_adx_value=IntParameter(15,50,default=30,space='buy')
    buy_fastk_value=IntParameter(15,50,default=30,space='buy')
    buy_fastd_value=IntParameter(15,50,default=30,space='buy')
    sell_fastk_value=IntParameter(50,90,default=70,space='sell')
    sell_fastd_value=IntParameter(50,90,default=70,space='sell')


    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        for val in self.ema_tp.range:
            dataframe[f'ema_high{val}'] = ta.EMA(dataframe, timeperiod=val, price='high')
            dataframe[f'ema_close{val}'] = ta.EMA(dataframe, timeperiod=val, price='close')
            dataframe[f'ema_low{val}'] = ta.EMA(dataframe, timeperiod=val, price='low')
        stoch_fast = ta.STOCHF(dataframe, 5, 3, 0, 3, 0)
        dataframe['fastd'] = stoch_fast['fastd']
        dataframe['fastk'] = stoch_fast['fastk']
        dataframe['adx'] = ta.ADX(dataframe)

        # required for graphing
        # bollinger = qtpylib.bollinger_bands(dataframe['close'], window=20, stds=2)
        # dataframe['bb_lowerband'] = bollinger['lower']
        # dataframe['bb_upperband'] = bollinger['upper']
        # dataframe['bb_middleband'] = bollinger['mid']

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions=[]
        conditions.append(dataframe['open'] < dataframe[f'ema_low{self.ema_tp.value}'])
        conditions.append(dataframe['adx'] > self.buy_adx_value.value)
        conditions.append(dataframe['fastk']<self.buy_fastk_value.value)
        conditions.append(dataframe['fastd']<self.buy_fastd_value.value)
        conditions.append(qtpylib.crossed_above(dataframe['fastk'], dataframe['fastd']))

        if conditions:
            dataframe.loc[reduce(lambda x,y:x&y,conditions),'buy']=1 


        # dataframe.loc[
        #     (
        #         (dataframe['open'] < dataframe['ema_low']) &
        #         (dataframe['adx'] > 30) &
        #         (
        #             (dataframe['fastk'] < 30) &
        #             (dataframe['fastd'] < 30) &
        #             (qtpylib.crossed_above(dataframe['fastk'], dataframe['fastd']))
        #         )
        #     ),
        #     'buy'] = 1
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe['open'] >= dataframe[f'ema_high{self.ema_tp.value}'])
            ) |
            (
                (qtpylib.crossed_above(dataframe['fastk'], self.sell_fastk_value.value)) |
                (qtpylib.crossed_above(dataframe['fastd'], self.sell_fastd_value.value))
            ),
            'sell'] = 1
        # dataframe.loc[
        #     (
        #         (dataframe['open'] >= dataframe['ema_high'])
        #     ) |
        #     (
        #         (qtpylib.crossed_above(dataframe['fastk'], 70)) |
        #         (qtpylib.crossed_above(dataframe['fastd'], 70))
        #     ),
        #     'sell'] = 1
        return dataframe
