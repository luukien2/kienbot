# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement

from functools import reduce
from typing import Any, Callable, Dict, List
# from datetime import datetime
import warnings
# import numpy as np
import talib.abstract as ta
from pandas import DataFrame
from skopt.space import Categorical, Dimension, Integer, Real

import freqtrade.vendor.qtpylib.indicators as qtpylib
from freqtrade.optimize.hyperopt_interface import IHyperOpt


class newHyperOpts(IHyperOpt):
    """
    You must keep:
    - The prototypes for the methods: populate_indicators,
        indicator_space, buy_strategy_generator.

    """
    warnings.simplefilter(action='ignore', category=UserWarning)
    warnings.simplefilter(action='ignore', category=DeprecationWarning)

    @staticmethod
    def populate_indicators(dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Add indicators needed for buy and sell strategies defined below.
        """
        # ADX
        dataframe['adx'] = ta.ADX(dataframe)
        # Awesome oscilator
        dataframe['ao'] = qtpylib.awesome_oscillator(dataframe)
        # # MACD
        # macd = ta.MACD(dataframe)
        # dataframe['macd'] = macd['macd']
        # dataframe['macdsignal'] = macd['macdsignal']
        # dataframe['macdhist'] = macd['macdhist']

        # Minus Directional Indicator / Movement
        dataframe['minus_di'] = ta.MINUS_DI(dataframe)

        # Plus Directional Indicator / Movement
        dataframe['plus_di'] = ta.PLUS_DI(dataframe)

        # # RSI
        dataframe['rsi'] = ta.RSI(dataframe)

        # Stochastic Fast
        stoch_fast = ta.STOCHF(dataframe)
        dataframe['fastd'] = stoch_fast['fastd']

        # Bollinger bands
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe),
                                            window=140,
                                            stds=2)
        dataframe['bb_lowerband'] = bollinger['lower']
        dataframe['bb_upperband'] = bollinger['upper']

        return dataframe

    @staticmethod
    def indicator_space() -> List[Dimension]:
        return [
            # # ADX
            Integer(1, 97, name='adx-value'),
            Categorical([True, False], name='adx-enabled'),
            # Awesome oscilator
            Integer(-1000, 0, name='ao-value'),
            Categorical([True, False], name='ao-enabled'),
            Categorical([True, False], name='ao_weighted_value'),
            Integer(1, 10, name='ao-multiplier'),
            # Plus/Minus Directional indicator
            Integer(1, 99, name='minus_di-value'),
            Categorical([True, False], name='minus_di-enabled'),
            Integer(1, 99, name='plus_di-value'),
            Categorical([True, False], name='plus_di-enabled'),
            # Fast Stochastic
            Integer(1, 99, name='fastd-value'),
            Categorical([True, False], name='fastd-enabled'),
            # Bollinger band
            Categorical(['bb_lower_cross'], name='trigger'),
            # RSI
            Categorical([True, False], name='rsi-enabled'),
            Integer(1, 99, name='rsi-value'),
        ]

    @staticmethod
    def buy_strategy_generator(params: Dict[str, Any]) -> Callable:
        def populate_buy_trend(dataframe: DataFrame,
                               metadata: dict) -> DataFrame:
            test_ind = {
                'ao':
                qtpylib.awesome_oscillator(
                    dataframe,
                    weighted=params['ao_weighted_value'],
                    fast=params['ao-multiplier'] * 5,
                    slow=params['ao-multiplier'] * 35)
            }
            conditions = []
            # GUARDS AND TRENDS
            lt_inds = ['ao', 'fastd', 'rsi', 'plus_di']
            for lt_ind in lt_inds:
                if f'{lt_ind}-enabled' in params and params[
                        f'{lt_ind}-enabled']:
                    if lt_ind in test_ind.keys():
                        conditions.append(
                            dataframe[lt_ind] < params[f'{lt_ind}-value'])
                    else:
                        conditions.append(
                            dataframe[lt_ind] < params[f'{lt_ind}-value'])

            gt_inds = ['minus_di', 'adx']
            for gt_ind in gt_inds:
                if f'{gt_ind}-enabled' in params and params[
                        f'{gt_ind}-enabled']:
                    if gt_ind in test_ind.keys():
                        conditions.append(
                            dataframe[gt_ind] > params[f'{gt_ind}-value'])
                    else:
                        conditions.append(
                            dataframe[gt_ind] > params[f'{gt_ind}-value'])
            # TRIGGERS
            if 'trigger' in params:
                if params['trigger'] == 'bb_lower_cross':
                    # bollinger = qtpylib.bollinger_bands(
                    #     qtpylib.typical_price(dataframe),
                    #     window=params['bb-window_value'],
                    #     stds=params['bb-stds_value'])
                    # dataframe['bb_lowerband'] = bollinger['lower']
                    conditions.append(
                        qtpylib.crossed_above(dataframe['close'],
                                              dataframe['bb_lowerband']))

            if conditions:
                dataframe.loc[reduce(lambda x, y: x & y, conditions
                                     ), 'buy'] = 1

            return dataframe

        return populate_buy_trend

    @staticmethod
    def sell_indicator_space() -> List[Dimension]:
        return [
            # # ADX
            Integer(1, 99, name='sell-adx-value'),
            Categorical([True, False], name='sell-adx-enabled'),
            # Awesomce oscilator
            Integer(0, 2000, name='sell-ao-value'),
            Categorical([True, False], name='sell-ao-enabled'),
            Categorical([True, False], name='sell-ao_weighted_value'),
            Integer(1, 10, name='sell-ao-multiplier'),
            # Plus/Minus Directional indicator
            Integer(30, 75, name='sell-minus_di-value'),
            Categorical([True, False], name='sell-minus_di-enabled'),
            Integer(60, 80, name='sell-plus_di-value'),
            Categorical([True, False], name='sell-plus_di-enabled'),
            # Stochastic Fast
            Integer(90, 100, name='sell-fastd-value'),
            Categorical([True, False], name='sell-fastd-enabled'),
            # Integer(80, 150, name='sell-bb-window_value'),
            # Integer(2, 5, name='sell-bb-stds_value')
            # Bollinger band
            Categorical(['sell-bb_upper_cross'], name='trigger'),
            Categorical([True, False], name='sell-rsi-enabled'),
            Integer(1, 99, name='sell-rsi-value'),
        ]

    @staticmethod
    def sell_strategy_generator(params: Dict[str, Any]) -> Callable:
        def populate_sell_trend(dataframe: DataFrame,
                                metadata: dict) -> DataFrame:
            sell_test_ind = {
                'ao':
                qtpylib.awesome_oscillator(
                    dataframe,
                    weighted=params['sell-ao_weighted_value'],
                    fast=params['sell-ao-multiplier'] * 5,
                    slow=params['sell-ao-multiplier'] * 35)
            }
            conditions = []

            # GUARDS AND TRENDS
            lt_inds = [
                'plus_di',
            ]
            for lt_ind in lt_inds:
                if f'sell-{lt_ind}-enabled' in params and params[
                        f'sell-{lt_ind}-enabled']:
                    if lt_ind in sell_test_ind.keys():
                        conditions.append(
                            dataframe[lt_ind] > params[f'{lt_ind}-value'])
                    else:
                        conditions.append(
                            dataframe[lt_ind] < params[f'sell-{lt_ind}-value'])

            gt_inds = ['ao', 'fastd', 'rsi', 'adx', 'minus_di']
            for gt_ind in gt_inds:
                if f'sell-{gt_ind}-enabled' in params and params[
                        f'sell-{gt_ind}-enabled']:
                    if gt_ind in sell_test_ind.keys():
                        conditions.append(
                            dataframe[gt_ind] > params[f'{gt_ind}-value'])
                    else:
                        conditions.append(
                            dataframe[gt_ind] > params[f'sell-{gt_ind}-value'])

            # TRIGGERS
            if 'sell-trigger' in params:
                if params['sell-trigger'] == 'sell-bb_upper_cross':
                    # bollinger = qtpylib.bollinger_bands(
                    #     qtpylib.typical_price(dataframe),
                    #     window=params['sell-bb-window_value'],
                    #     stds=params['sell-bb-stds_value'])
                    # dataframe['bb_upperband'] = bollinger['upper']
                    conditions.append(
                        dataframe['close'] > dataframe['bb_upperband'])

            if conditions:
                dataframe.loc[reduce(lambda x, y: x & y, conditions
                                     ), 'sell'] = 1

            return dataframe

        return populate_sell_trend

    def populate_buy_trend(self, dataframe: DataFrame,
                           metadata: dict) -> DataFrame:
        """
        Based on TA indicators. Should be a copy of same method from strategy.
        Must align to populate_indicators in this file.
        Only used when --spaces does not include buy space.
        """
        dataframe.loc[(dataframe['fastd'] < 19) & (qtpylib.crossed_above(
            dataframe['close'], dataframe['bb_lowerband'])), 'buy'] = 1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame,
                            metadata: dict) -> DataFrame:
        """
        Based on TA indicators. Should be a copy of same method from strategy.
        Must align to populate_indicators in this file.
        Only used when --spaces does not include sell space.
        """
        dataframe.loc[(
            (dataframe['fastd'] > 99) &
            (dataframe['close'] > dataframe['bb_upperband'])), 'sell'] = 1
        return dataframe
