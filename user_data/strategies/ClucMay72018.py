# --- Do not remove these libs ---
from freqtrade.strategy.interface import IStrategy
from freqtrade.strategy import IntParameter, CategoricalParameter, DecimalParameter
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


class ClucMay72018(IStrategy):
    """

    author@: Gert Wohlgemuth

    works on new objectify branch!

    """

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi"
    minimal_roi = {
        "0": 0.01
    }

    # Optimal stoploss designed for the strategy
    # This attribute will be overridden if the config file contains "stoploss"
    stoploss = -0.05

    # Optimal timeframe for the strategy
    timeframe = '5m'

    bb_std=IntParameter(1,3,default=2,space='sell')
    buy_close_gap=DecimalParameter (0.8,1,default=0.985,space='buy')
    buy_ema_tp=IntParameter(30,100,default=50,space='buy')
    buy_volume_window=IntParameter(10,50,default=30,space='buy')



    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # dataframe['rsi'] = ta.RSI(dataframe, timeperiod=5)
        # rsiframe = DataFrame(dataframe['rsi']).rename(columns={'rsi': 'close'})
        # dataframe['emarsi'] = ta.EMA(rsiframe, timeperiod=5)
        # macd = ta.MACD(dataframe)
        # dataframe['macd'] = macd['macd']
        # dataframe['adx'] = ta.ADX(dataframe)
        for val in self.bb_std.range:
            bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=val)
            dataframe[f'bb_lower{val}'] = bollinger['lower']
            dataframe[f'bb_middle{val}'] = bollinger['mid']
            dataframe[f'bb_upper{val}'] = bollinger['upper']
        for val in self.buy_ema_tp.range:
            dataframe[f'buy_ema{val}'] = ta.EMA(dataframe, timeperiod=val)
        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the buy signal for the given dataframe
        :param dataframe: DataFrame
        :return: DataFrame with buy column
        """
        conditions=[]
        conditions.append(dataframe['close']<dataframe[f'buy_ema{self.buy_ema_tp.value}'])
        conditions.append(dataframe['close']<self.buy_close_gap.value*dataframe[f'bb_lower{self.bb_std.value}'])
        conditions.append(dataframe['volume']<(dataframe['volume'].rolling(window=self.buy_volume_window.value).mean().shift(1)*20))
        dataframe.loc[reduce(lambda x,y: x&y,conditions),'buy']=1
        # dataframe.loc[
        #     (
        #             (dataframe['close'] < dataframe['ema100']) &
        #             (dataframe['close'] < 0.985 * dataframe['bb_lowerband']) &
        #             (dataframe['volume'] < (dataframe['volume'].rolling(window=30).mean().shift(1) * 20))
        #     ),
        #     'buy'] = 1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the sell signal for the given dataframe
        :param dataframe: DataFrame
        :return: DataFrame with buy column
        """
        dataframe.loc[
            (
                (dataframe['close'] > dataframe[f'bb_middle{self.bb_std.value}'])
            ),
            'sell'] = 1
        return dataframe
