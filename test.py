# --- Do not remove these libs ---
from freqtrade.strategy.interface import IStrategy
from typing import Dict, List
from functools import reduce
from pandas import DataFrame
# --------------------------------

import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib

class CunConTrade(IStrategy):

    minimal_roi = {
        "60":  0.1,
        "30":  0.08,
        "20":  0.06,
        "0":  0.3
    }

    stoploss = -0.10

    ticker_interval = '15m'

    trailing_stop = True
    trailing_stop_positive = 0.06
    trailing_stop_positive_offset = 0.09

    # run "populate_indicators" only for new candle
    ta_on_candle = False

    # Experimental settings (configuration will overide these if set)
    use_sell_signal = True
    sell_profit_only = True
    ignore_roi_if_buy_signal = False

    # Optional order type mapping
    order_types = {
        'buy': 'limit',
        'sell': 'limit',
        'stoploss': 'market',
        'stoploss_on_exchange': False
    }

    def informative_pairs(self):
        """
        Define additional, informative pair/interval combinations to be cached from the exchange.
        These pair/interval combinations are non-tradeable, unless they are part
        of the whitelist as well.
        For more information, please consult the documentation
        :return: List of tuples in the format (pair, interval)
            Sample: return [("ETH/USDT", "5m"),
                            ("BTC/USDT", "15m"),
                            ]
        """
        return [(f"{self.config['stake_currency']}/USDT", self.ticker_interval)]
                 
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['adx'] = ta.ADX(dataframe, timeperiod=14)
        dataframe['short'] = ta.SMA(dataframe, timeperiod=3)
        dataframe['long'] = ta.SMA(dataframe, timeperiod=6)
        dataframe['ao'] = qtpylib.awesome_oscillator(dataframe)
        macd = ta.MACD(dataframe)
        dataframe['macd'] = macd['macd']
        dataframe['macdsignal'] = macd['macdsignal']
        dataframe['macdhist'] = macd['macdhist']
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_low'] = bollinger['lower']
        dataframe['bb_mid'] = bollinger['mid']
        dataframe['bb_upper'] = bollinger['upper']
        # %B = (Current Price - Lower Band) / (Upper Band - Lower Band)
        dataframe['bb_perc'] = (dataframe['close'] - dataframe['bb_low']) / (dataframe['bb_upper'] - dataframe['bb_low'])
        return dataframe
    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                    ((dataframe['adx'] > 25) &
                    qtpylib.crossed_above(dataframe['short'], dataframe['long'])) |
                    (
                        (dataframe['macd'] > 0) &
                        ((dataframe['macd'] > dataframe['macdsignal']) |
                         ((dataframe['ao'] > 0) &
                        (dataframe['ao'].shift() < 0))) |
                        (dataframe['bb_perc'] < 0.1)
                    )
            ),
            'buy'] = 1
        return dataframe
    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                ((dataframe['adx'] < 25) &
                    (qtpylib.crossed_above(dataframe['long'], dataframe['short']))) |
                (
                        (dataframe['macd'] < 0) &
                        ((dataframe['macd'] < dataframe['macdsignal']) |
                         ((dataframe['ao'] < 0) &
                          (dataframe['ao'].shift() > 0)))
                        (dataframe['close'] > dataframe['high'].rolling(60).max().shift())
                  )
               ),
               'sell'] = 1
           return dataframe
