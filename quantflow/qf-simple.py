#!/usr/bin/env python
from datetime import datetime
from pprint import pformat
from qtpylib import futures
from qtpylib.algo import Algo
import logging
import os
import sys
BASE_DIR = os.path.dirname(os.path.realpath(__file__))

FORMAT = '%(asctime)-15s %(levelname)-5s -> %(message)s'

logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

class CrossOver(Algo):

    def on_start(self):
        pass

    def on_fill(self, instrument, order):
        pass

    def on_quote(self, instrument):
        pass

    def on_orderbook(self, instrument):
        pass

    def on_tick(self, instrument):
        logger.info('LY: on_tick {}'.format(datetime.now()))
        pass

    def on_bar(self, instrument):
        logger.info('LY: on_bar CrossOver {}'.format(datetime.now()))
        # get instrument history
        #bars = instrument.get_bars(lookback=30)

        # or get all instruments history
        #bars = self.bars[-20:]
        bars = self.bars

        # skip first 20 days to get full windows
        logger.info('LY: len(bars) is {}'.format(len(bars)))
        #logger.info('LY: last bar is {}'.format(bars[-1]))
        #if len(bars) < 20:
            #return

        # compute averages using internal rolling_mean
        bars['short_ma'] = bars['close'].rolling_mean(window=10)
        bars['long_ma']  = bars['close'].rolling_mean(window=20)

        logger.info('LY: short_ma is {}'.format(bars['short_ma'][-1]))
        logger.info(bars.tail())

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
    parser.set_defaults(debug=True, symbol='CL', preload='1D')
    args = parser.parse_args()
    return args


if __name__ == "__main__":

    args = make_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    logger.debug("It works!")

    logger.info('Getting ready to run: {}'.format(args.symbol))

    ib_tuple = futures.make_tuple(args.symbol)
    logger.info("Tuple is {}".format(ib_tuple))

    strategy = CrossOver(
        instruments = [ ib_tuple, ],
        resolution  = "1T",
        bar_window  = 50,
        preload     = args.preload, # 1W, 1D, 3D
        ibport    = 7497,
        blotter='MainBlotter',
    )

    logger.info("Running...")
    strategy.run()
    logger.info('Finished')

