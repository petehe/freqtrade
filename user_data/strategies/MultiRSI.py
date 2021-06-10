# --- Do not remove these libs ---
from freqtrade.strategy.hyper import IntParameter
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame
# --------------------------------
import talib.abstract as ta
from technical.util import resample_to_interval, resampled_merge
from functools import reduce

class MultiRSI(IStrategy):
    """

    author@: Gert Wohlgemuth

    based on work from Creslin

    """
    minimal_roi = {
        "0": 0.01
    }

    # Optimal stoploss designed for the strategy
    stoploss = -0.05

    # Optimal timeframe for the strategy
    timeframe = '5m'

    def get_ticker_indicator(self):
        return int(self.timeframe[:-1])

    buy_sma_short=IntParameter(3,50,default=5,space='buy')
    buy_sma_long=IntParameter(51,200,default=5,space='buy')


    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        for val in self.buy_sma_short.range:
            dataframe[f'buy_sma{val}'] = ta.SMA(dataframe, timeperiod=val)
        for val in self.buy_sma_long.range:
            dataframe[f'buy_sma{val}'] = ta.SMA(dataframe, timeperiod=val)


        # resample our dataframes
        dataframe_short = resample_to_interval(dataframe, self.get_ticker_indicator() * 2)
        dataframe_long = resample_to_interval(dataframe, self.get_ticker_indicator() * 8)

        # compute our RSI's
        dataframe_short['rsi'] = ta.RSI(dataframe_short, timeperiod=14)
        dataframe_long['rsi'] = ta.RSI(dataframe_long, timeperiod=14)

        # merge dataframe back together
        dataframe = resampled_merge(dataframe, dataframe_short)
        dataframe = resampled_merge(dataframe, dataframe_long)

        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)

        dataframe.fillna(method='ffill', inplace=True)

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions=[]
        conditions.append(dataframe[f'buysma{self.buy_sma_short.value}'] >= dataframe[f'buysma{self.buy_sma_long.value}'])
        conditions.append(dataframe['rsi'] < (dataframe['resample_{}_rsi'.format(self.get_ticker_indicator() * 8)] - 20))

        if conditions:
            dataframe.loc[reduce(lambda x,y:x&y,conditions),'buy']=1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions=[]
        conditions.append(dataframe['rsi'] > dataframe['resample_{}_rsi'.format(self.get_ticker_indicator()*2)])
        conditions.append(dataframe['rsi'] > dataframe['resample_{}_rsi'.format(self.get_ticker_indicator()*8)])

        if conditions:
            dataframe.loc[reduce(lambda x,y:x&y,conditions),'sell']=1

        return dataframe
