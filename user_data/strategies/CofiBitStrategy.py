# --- Do not remove these libs ---
import freqtrade.vendor.qtpylib.indicators as qtpylib
import talib.abstract as ta
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame
from freqtrade.strategy import CategoricalParameter, IntParameter
from functools import reduce

# --------------------------------


class CofiBitStrategy(IStrategy):
    """
        taken from slack by user CofiBit
    """

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi"
    minimal_roi = {
        "40": 0.05,
        "30": 0.06,
        "20": 0.07,
        "0": 0.10
    }

    # Optimal stoploss designed for the strategy
    # This attribute will be overridden if the config file contains "stoploss"
    stoploss = -0.25

    # Optimal timeframe for the strategy
    timeframe = '5m'

    buy_ema_tp=IntParameter(3,10,default=5,space='buy')
    buy_fastk_value=IntParameter(10,50,default=30,space='buy')
    buy_fastd_value=IntParameter(10,50,default=30,space='buy')
    buy_adx_value=IntParameter(10,50,default=30,space='buy')

    sell_fastk_value=IntParameter(50,100,default=70,space='sell')
    sell_fastd_value=IntParameter(50,100,default=70,space='sell')

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        stoch_fast = ta.STOCHF(dataframe, 5, 3, 0, 3, 0)
        dataframe['fastd'] = stoch_fast['fastd']
        dataframe['fastk'] = stoch_fast['fastk']
        for val in self.buy_ema_tp.range:
            dataframe[f'ema_high{val}'] = ta.EMA(dataframe, timeperiod=val, price='high')
            dataframe[f'ema_close{val}'] = ta.EMA(dataframe, timeperiod=val, price='close')
            dataframe[f'ema_low{val}'] = ta.EMA(dataframe, timeperiod=val, price='low')
        dataframe['adx'] = ta.ADX(dataframe)

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the buy signal for the given dataframe
        :param dataframe: DataFrame
        :return: DataFrame with buy column
        """
        conditions=[]
        conditions.append(dataframe['open'] < dataframe[f'ema_low{self.buy_ema_tp.value}']) 
        conditions.append(qtpylib.crossed_above(dataframe['fastk'], dataframe['fastd'])) 
        conditions.append(dataframe['fastk'] < self.buy_fastk_value.value) 
        conditions.append(dataframe['fastd'] < self.buy_fastd_value.value) 
        conditions.append(dataframe['adx'] > self.buy_adx_value.value)
        if conditions:
            dataframe.loc[reduce(lambda x,y:x&y,conditions),'buy']=1

        # dataframe.loc[
        #     (
        #         (dataframe['open'] < dataframe['ema_low']) &
        #         (qtpylib.crossed_above(dataframe['fastk'], dataframe['fastd'])) &
        #         # (dataframe['fastk'] > dataframe['fastd']) &
        #         (dataframe['fastk'] < 30) &
        #         (dataframe['fastd'] < 30) &
        #         (dataframe['adx'] > 30)
        #     ),
        #     'buy'] = 1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the sell signal for the given dataframe
        :param dataframe: DataFrame
        :return: DataFrame with buy column
        """
        c1=dataframe['open'] >= dataframe[f'ema_high{self.buy_ema_tp.value}']
        c2=(qtpylib.crossed_above(dataframe['fastk'], self.sell_fastk_value.value))|(qtpylib.crossed_above(dataframe['fastd'],self.sell_fastd_value.value ))
        conditions=c1|c2
        dataframe.loc[conditions,'sell']=1

        # dataframe.loc[
        #     (
        #         (dataframe['open'] >= dataframe['ema_high'])
        #     ) |
        #     (
        #         # (dataframe['fastk'] > 70) &
        #         # (dataframe['fastd'] > 70)
        #             (qtpylib.crossed_above(dataframe['fastk'], 70)) |
        #             (qtpylib.crossed_above(dataframe['fastd'], 70))
        #     ),
        #     'sell'] = 1

        return dataframe
