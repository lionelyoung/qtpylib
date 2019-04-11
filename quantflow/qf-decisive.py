#!/usr/bin/env python
from datetime import datetime
from pprint import pformat
from qtpylib import futures
from qtpylib.algo import Algo
import logging
import os
import sys
from pprint import pformat
import numpy as np
import pandas as pd
from sklearn.externals import joblib
import time

BASE_DIR = os.path.dirname(os.path.realpath(__file__))

FORMAT = '%(asctime)-15s %(levelname)-5s [%(name)s] -> %(message)s'

logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

class QFSimpleCross(Algo):

    def __init__(self, **kwargs):
        Algo.__init__(self, **kwargs)
        if kwargs['classifier']:
            self.clf = kwargs['classifier']
        else:
            self.clf = None
        logger.info('Initialize with classifier: {}'.format(self.clf))

    def on_start(self):
        pass

    def on_fill(self, instrument, order):
        pass

    def on_quote(self, instrument):
        pass

    def on_orderbook(self, instrument):
        pass

    def on_tick(self, instrument):
        #logger.debug('TICK {}'.format(datetime.now()))
        sec = int(time.time()) % 10
        print(sec, end='', flush=True)

    def on_bar(self, instrument):

        # Features
        features = {'ai_squeeze':  -0.176471,
                    'ai_explosive': -0.003112,
                    'side': None,
                    'sma': None,
                    }

        # Set subset of bars
        bars = self.bars[-60:]

        # skip first 20 days to get full windows
        logger.info('01 Got bar')
        if len(bars) < 50:
            logger.info('Skip bars')
            return

        logger.info('02 Got bar')

        # compute averages using internal rolling_mean
        bars['short_ma'] = bars['close'].rolling_mean(window=20)
        bars['long_ma']  = bars['close'].rolling_mean(window=50)

        # Features
        short_above_long = bars['short_ma'] > bars['long_ma']
        bars['sma'] = np.where(short_above_long, 1, -1)
        close_higher = bars['close'] > bars['close'].shift(5)
        bars['side'] = np.where(close_higher, 1, -1)

        last_bar = bars.tail(1)

        logger.info('03 sma')
        # Feature: sma
        #import pdb; pdb.set_trace() 
        features['sma'] = int(last_bar['sma'])
        logger.info('Features: {}'.format(pformat(features)))

        logger.info('04 side')
        # Feature: side
        features['side'] = int(last_bar['side'])
        logger.info('Features: {}'.format(pformat(features)))

        # Create temp dataframe with freatures
        logger.info('Classifier is: {}'.format(self.clf))

        new_data = pd.DataFrame(columns=['ai_squeeze', 'ai_explosive', 'side', 'sma'])
        new_data.loc[len(new_data)] = [features['ai_squeeze'],
                                       features['ai_explosive'],
                                       features['side'],
                                       features['sma']]

        my_predict = rf.predict(new_data)
        logger.info('Prediction is: {}'.format(my_predict))

        # get current position data
        positions = instrument.get_positions()
        logger.info('Positions are: {}'.format(positions))

        #########
        # TRADE #
        #########

        if my_predict and not instrument.pending_orders and positions["position"] == 0:
            logger.info('BUY Every Bar {}'.format(datetime.now()))
            instrument.buy(1)
            self.record(all_buy=1)
        else:
            logger.info("NO TRADE")

        if positions["position"] != 0:
            logger.info('CLOSE Every Bar {}'.format(datetime.now()))
            instrument.exit()
            self.record(all_buy=-1)

def make_args():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true", help="increase output verbosity")
    parser.add_argument("--symbol", action="store")
    parser.add_argument("--preload", action="store")
    parser.add_argument("--resolution", action="store")
    parser.add_argument("--bar-window", action="store", type=int)
    parser.add_argument("--ibport", action="store", type=int)
    parser.set_defaults(debug=False, symbol='CL', preload='1D', resolution='1T', bar_window=60, ibport=7497)
    args = parser.parse_args()
    return args


if __name__ == "__main__":

    args = make_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)
        logging.getLogger('ly_algo').setLevel(logging.DEBUG)
        logging.getLogger('ly_broker').setLevel(logging.DEBUG)
        logging.getLogger('ly_blotter').setLevel(logging.DEBUG)
        logging.getLogger('ly_workflow').setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
        logging.getLogger('ly_algo').setLevel(logging.INFO)
        logging.getLogger('ly_broker').setLevel(logging.INFO)
        logging.getLogger('ly_blotter').setLevel(logging.INFO)
        logging.getLogger('ly_workflow').setLevel(logging.INFO)


    # Make tuple in qtpy format
    ib_tuple = futures.make_tuple(args.symbol)

    # Display settings
    logger.info('Settings')
    logger.info('--------')
    logger.info('\tSymbol: {}'.format(args.symbol))
    logger.info('\tResolution: {}'.format(args.resolution))
    logger.info('\tPreload: {}'.format(args.preload))
    logger.info('\tFutures tuple: {}'.format(ib_tuple))

    # Load Model
    rf = joblib.load(os.path.join(BASE_DIR, "../../bw_research/models/20190410-215948_02p02_DecisiveAlpha.pkl"))
    logger.info('Classifier is: {}'.format(rf))
    # Setup Algo
    strategy = QFSimpleCross(instruments=[ ib_tuple, ],
                             resolution=args.resolution,
                             bar_window=args.bar_window,
                             preload=args.preload,
                             ibport=args.ibport,
                             blotter='MainBlotter',
                             # My variables
                             classifier=rf,)

    # Run
    logger.info("Run")
    strategy.run()


