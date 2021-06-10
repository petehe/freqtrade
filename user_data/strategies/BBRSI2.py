# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement

from freqtrade.strategy.hyper import CategoricalParameter, IntParameter
import talib.abstract as ta
import pandas
from pandas import DataFrame

import freqtrade.vendor.qtpylib.indicators as qtpylib
from freqtrade.strategy.interface import IStrategy
from functools import reduce
pandas.set_option("display.precision",8)

class BBRSI2(IStrategy):
    """
    Default Strategy provided by freqtrade bot.
    You can override it with your own strategy
    """

    # Minimal ROI designed for the strategy
    minimal_roi = {
        "0": 0.0963,
        "38": 0.07377,
        "55": 0.01135,
        "120": 0
    }

    # Optimal stoploss designed for the strategy
    stoploss = -0.38067

    # Optimal ticker interval for the strategy
    ticker_interval = '1h'

    # Optional order type mapping
    order_types = {
        'buy': 'limit',
        'sell': 'limit',
        'stoploss': 'limit',
        'stoploss_on_exchange': False
    }

    # Optional time in force for orders
    order_time_in_force = {
        'buy': 'gtc',
        'sell': 'gtc',
    }

    #define hyperopt parameters
    buy_bbband=CategoricalParameter(['upper','lower','mid'],default='lower',space='buy')
    sell_bbband=CategoricalParameter(['upper','lower','mid'],default='lower',space='sell')

    buy_bbstd=IntParameter(1,4, default=2,space='buy')
    sell_bbstd=IntParameter(1,4, default=2,space='sell')
    buy_rsi_value=IntParameter(5,50, default=30,space='buy')
    sell_rsi_value=IntParameter(30,100, default=70,space='sell')
    buy_rsi_enabled=CategoricalParameter([True,False],default=True,space='buy')
    sell_rsi_enabled=CategoricalParameter([True,False],default=True,space='sell')


    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Adds several different TA indicators to the given DataFrame

        Performance Note: For the best performance be frugal on the number of indicators
        you are using. Let uncomment only the indicator you are using in your strategies
        or your hyperopt configuration, otherwise you will waste your memory and CPU usage.
        :param dataframe: Raw data from the exchange and parsed by parse_ticker_dataframe()
        :param metadata: Additional information, like the currently traded pair
        :return: a Dataframe with all mandatory indicators for the strategies
        """

        # Momentum Indicator
        # ------------------------------------
        # RSI
        dataframe['rsi'] = ta.RSI(dataframe)

        # Bollinger bands
        for std in self.buy_bbstd.range:
            bollinger= qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=std)
            for band in self.buy_bbband.opt_range:
                dataframe[f'buybb_{band}band{std}'] = bollinger[band]

        for std in self.sell_bbstd.range:
            bollinger= qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=std)
            for band in self.buy_bbband.opt_range:
                dataframe[f'sellbb_{band}band{std}'] = bollinger[band]
        dataframe.to_csv('bbrsi_ind.csv')
        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the buy signal for the given dataframe
        :param dataframe: DataFrame
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with buy column
        """
        conditions=[]
        if self.buy_rsi_enabled:
            conditions.append(dataframe['rsi']>self.buy_rsi_value.value)
        conditions.append(dataframe['close']<dataframe[f'buybb_{self.buy_bbband.value}band{self.buy_bbstd.value}'])

        if conditions:
            dataframe.loc[reduce(lambda x,y:x&y,conditions),'buy']=1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the sell signal for the given dataframe
        :param dataframe: DataFrame
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with buy column
        """
        conditions=[]
        if self.sell_rsi_enabled:
            conditions.append(dataframe['rsi']>self.sell_rsi_value.value)
        conditions.append(dataframe['close']>dataframe[f'sellbb_{self.sell_bbband.value}band{self.sell_bbstd.value}'])

        if conditions:
            dataframe.loc[reduce(lambda x,y:x&y,conditions),'buy']=1

        return dataframe
