# --- Do not remove these libs ---
from freqtrade.strategy.interface import IStrategy
from typing import Dict, List
from functools import reduce
from pandas import DataFrame
# --------------------------------

import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from freqtrade.strategy import CategoricalParameter, IntParameter


class Simple(IStrategy):
    """

    author@: Gert Wohlgemuth

    idea:
        this strategy is based on the book, 'The Simple Strategy' and can be found in detail here:

        https://www.amazon.com/Simple-Strategy-Powerful-Trading-Futures-ebook/dp/B00E66QPCG/ref=sr_1_1?ie=UTF8&qid=1525202675&sr=8-1&keywords=the+simple+strategy
    """

    # Minimal ROI designed for the strategy.
    # adjust based on market conditions. We would recommend to keep it low for quick turn arounds
    # This attribute will be overridden if the config file contains "minimal_roi"
    minimal_roi = {
        "0": 0.01
    }

    # Optimal stoploss designed for the strategy
    # This attribute will be overridden if the config file contains "stoploss"
    stoploss = -0.25

    # Optimal timeframe for the strategy
    timeframe = '5m'
    
    #MACD
    buy_macd_enabled=CategoricalParameter([True,False],default=True,space='buy')
    sell_macd_enabled=CategoricalParameter([True,False],default=False,space='sell')
    
    #BB
    buy_bb_enabled=CategoricalParameter([True,False],default=True,space='buy')
    sell_bb_enabled=CategoricalParameter([True,False],default=False,space='sell')
    bbstd=IntParameter(1,4, default=2,space='buy')
    bbwindow=IntParameter(7,20,default=12, space='buy')

    #RSI
    rsi_tp=IntParameter(3,14, default=7,space='buy')
    buy_rsi_enabled=CategoricalParameter([True,False],default=True,space='buy')
    buy_rsi_value=IntParameter(30,100, default=70,space='buy')
    sell_rsi_enabled=CategoricalParameter([True,False],default=True,space='sell')
    sell_rsi_value=IntParameter(30,100, default=80,space='sell')
    


    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # MACD
        macd = ta.MACD(dataframe)
        dataframe['macd'] = macd['macd']
        dataframe['macdsignal'] = macd['macdsignal']
        dataframe['macdhist'] = macd['macdhist']

        # RSI
        for val in self.rsi_tp.range:
            dataframe[f'rsi{val}'] = ta.RSI(dataframe, timeperiod=val)

        # Bollinger bands
        for std in self.bbstd.range:
            for window in self.bbwindow.range:
                bollinger = qtpylib.bollinger_bands(dataframe['close'], window=window, stds=std)
                dataframe[f'bb{window}upper{std}'] = bollinger['upper']
                dataframe[f'bb{window}lower{std}'] = bollinger['lower']
        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions=[]
        if self.buy_bb_enabled.value:
            conditions.append(dataframe['macd']>0)
            conditions.append(dataframe['macd'] > dataframe['macdsignal'])
        if self.buy_bb_enabled.value:
            conditions.append(dataframe[f'bb{self.bbwindow.value}upper{self.bbstd.value}'] > dataframe[f'bb{self.bbwindow.value}upper{self.bbstd.value}'].shift(1))
        if self.buy_rsi_enabled.value:
            conditions.append(dataframe[f'rsi{self.rsi_tp.value}']>self.buy_rsi_value.value)

        if conditions:
            dataframe.loc[reduce(lambda x,y:x&y,conditions),'buy']=1
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # different strategy used for sell points, due to be able to duplicate it to 100%
        # dataframe.loc[
        #     (
        #         (dataframe['rsi'] > 80)
        #     ),
        #     'sell'] = 1
        # return dataframe
        conditions=[]
        if self.sell_bb_enabled.value:
            conditions.append(dataframe['macd']<0)
            conditions.append(dataframe['macd'] < dataframe['macdsignal'])
        if self.sell_bb_enabled.value:
            conditions.append(dataframe[f'bb{self.bbwindow.value}lower{self.bbstd.value}'] < dataframe[f'bb{self.bbwindow.value}lower{self.bbstd.value}'].shift(1))
        if self.sell_rsi_enabled.value:
            conditions.append(dataframe[f'rsi{self.rsi_tp.value}']>self.sell_rsi_value.value)
        if conditions:
            dataframe.loc[reduce(lambda x,y:x&y,conditions),'sell']=1
        return dataframe
