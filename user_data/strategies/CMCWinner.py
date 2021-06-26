
# --- Do not remove these libs ---
from functools import reduce
from freqtrade.strategy.hyper import CategoricalParameter, IntParameter
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame
# --------------------------------

# Add your lib to import here
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
import numpy # noqa


# This class is a sample. Feel free to customize it.
class CMCWinner(IStrategy):
    """
    This is a test strategy to inspire you.
    More information in https://github.com/freqtrade/freqtrade/blob/develop/docs/bot-optimization.md

    You can:
    - Rename the class name (Do not forget to update class_name)
    - Add any methods you want to build your strategy
    - Add any lib you need to build your strategy

    You must keep:
    - the lib in the section "Do not remove these libs"
    - the prototype for the methods: minimal_roi, stoploss, populate_indicators, populate_buy_trend,
    populate_sell_trend, hyperopt_space, buy_strategy_generator
    """

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi"
    minimal_roi = {
        "40": 0.0,
        "30": 0.02,
        "20": 0.03,
        "0": 0.05
    }

    # Optimal stoploss designed for the strategy
    # This attribute will be overridden if the config file contains "stoploss"
    stoploss = -0.05

    # Optimal timeframe for the strategy
    timeframe = '15m'

    buy_cci_enabled=CategoricalParameter([True,False],default=True,space='buy')
    buy_cci_value=IntParameter(-200,-50,default=-100,space='buy')
    buy_mfi_enabled=CategoricalParameter([True,False],default=True,space='buy')
    buy_mfi_value=IntParameter(0,50,default=20,space='buy')
    buy_cmo_enabled=CategoricalParameter([True,False],default=True,space='buy')
    buy_cmo_value=IntParameter(-100,0,default=-50,space='buy')

    sell_cci_enabled=CategoricalParameter([True,False],default=True,space='sell')
    sell_cci_value=IntParameter(50, 200,default=100,space='sell')
    sell_mfi_enabled=CategoricalParameter([True,False],default=True,space='sell')
    sell_mfi_value=IntParameter(50,100,default=80,space='sell')
    sell_cmo_enabled=CategoricalParameter([True,False],default=True,space='sell')
    sell_cmo_value=IntParameter(0,100,default=50,space='sell')

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Adds several different TA indicators to the given DataFrame

        Performance Note: For the best performance be frugal on the number of indicators
        you are using. Let uncomment only the indicator you are using in your strategies
        or your hyperopt configuration, otherwise you will waste your memory and CPU usage.
        """

        # Commodity Channel Index: values Oversold:<-100, Overbought:>100
        dataframe['cci'] = ta.CCI(dataframe)

        # MFI
        dataframe['mfi'] = ta.MFI(dataframe)

		# CMO
        dataframe['cmo'] = ta.CMO(dataframe)

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the buy signal for the given dataframe
        :param dataframe: DataFrame
        :return: DataFrame with buy column
        """
        # dataframe.loc[
        #     (
        #         (dataframe['cci'].shift(1) < -100) &
        #         (dataframe['mfi'].shift(1) < 20) &
        #         (dataframe['cmo'].shift(1) < -50)
        #     ),
        #     'buy'] = 1
        # dataframe.loc[
        #     (
        #         (dataframe['cci'].shift(1) < self.buy_cci_value.value if self.buy_cci_enabled.value else True) &
        #         (dataframe['mfi'].shift(1) < self.buy_mfi_value.value if self.buy_mfi_enabled.value else True) &
        #         (dataframe['cmo'].shift(1) < self.buy_cmo_value.value if self.buy_cmo_enabled.value else True)
        #     ),
        #     'buy'] = 1
        conditions=[]
        if self.buy_cci_enabled.value:
            conditions.append(dataframe['cci'].shift(1) < self.buy_cci_value.value)
        if self.buy_mfi_enabled.value:
            conditions.append(dataframe['mfi'].shift(1) < self.buy_mfi_value.value)
        if self.buy_cmo_enabled.value:
            conditions.append(dataframe['cmo'].shift(1) < self.buy_cmo_value.value)
        
        if conditions:
            dataframe.loc[reduce(lambda x,y: x&y,conditions),'buy']=1
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the sell signal for the given dataframe
        :param dataframe: DataFrame
        :return: DataFrame with buy column
        """
        # dataframe.loc[
        #     (
        #         (dataframe['cci'].shift(1) > self.sell_cci_value.value if self.sell_cci_enabled.value else True) &
        #         (dataframe['mfi'].shift(1) > self.sell_mfi_value.value if self.sell_mfi_enabled.value else True) &
        #         (dataframe['cmo'].shift(1) > self.sell_cmo_value.value if self.sell_cmo_enabled.value else True)
        #     ),
        #     'sell'] = 1
        conditions=[]
        if self.sell_cci_enabled.value:
            conditions.append(dataframe['cci'].shift(1) > self.sell_cci_value.value)
        if self.sell_mfi_enabled.value:
            conditions.append(dataframe['mfi'].shift(1) >self.sell_mfi_value.value)
        if self.sell_cmo_enabled.value:
            conditions.append(dataframe['cmo'].shift(1) > self.sell_cmo_value.value)
        
        if conditions:
            dataframe.loc[reduce(lambda x,y: x&y,conditions),'sell']=1
        return dataframe
