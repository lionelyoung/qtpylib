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

BASE_DIR = os.path.dirname(os.path.realpath(__file__))

FORMAT = '%(asctime)-15s %(levelname)-5s [%(name)s] -> %(message)s'

logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

class QFSimpleCross(Algo):

    def on_start(self):
        pass

    def on_fill(self, instrument, order):
        pass

    def on_quote(self, instrument):
        pass

    def on_orderbook(self, instrument):
        pass

    def on_tick(self, instrument):
        logger.info('TICK {}'.format(datetime.now()))
        pass

    def on_bar(self, instrument):

        # Features
        features = {'sma': None,
                    'side': None,
                    'ai_squeeze':  -0.176471,
                    'ai_explosive': -0.003112,
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

        # get current position data
        positions = instrument.get_positions()

        if not instrument.pending_orders and positions["position"] == 0:
            logger.info('LY: instrument BUY every bar {}'.format(datetime.now()))
            instrument.buy(1)
            self.record(all_buy=1)

        if positions["position"] != 0:
            logger.info('LY: instrument EXIT {}'.format(datetime.now()))
            instrument.exit()
            self.record(all_buy=-1)

        # trading logic - entry signal
        if bars['short_ma'].crossed_above(bars['long_ma'])[-1]:
            if not instrument.pending_orders and positions["position"] == 0:

                logger.info('LY: instrument BUY {}'.format(datetime.now()))
                # buy one contract
                instrument.buy(1)

                logger.info('LY: recording ma_cross=1')
                # record values for later analysis
                self.record(ma_cross=1)

        # trading logic - exit signal
        elif bars['short_ma'].crossed_below(bars['long_ma'])[-1]:
            if positions["position"] != 0:

                logger.info('LY: instrument EXIT {}'.format(datetime.now()))
                # exit / flatten position
                instrument.exit()

                # record values for later analysis
                logger.info('LY: recording ma_cross=-1')
                self.record(ma_cross=-1)

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

    # Setup Algo
    strategy = QFSimpleCross(instruments=[ ib_tuple, ],
                             resolution=args.resolution,
                             bar_window=args.bar_window,
                             preload=args.preload,
                             ibport=args.ibport,
                             blotter='MainBlotter')

    # Run
    logger.info("Run")
    strategy.run()

