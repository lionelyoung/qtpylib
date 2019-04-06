# strategy.py
from qtpylib.algo import Algo
from qtpylib import futures
from datetime import datetime

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
        print('LY: on_tick {}'.format(datetime.now()))
        pass

    def on_bar(self, instrument):
        print('LY: on_bar CrossOver {}'.format(datetime.now()))
        # get instrument history
        #bars = instrument.get_bars(lookback=30)

        # or get all instruments history
        #bars = self.bars[-20:]
        bars = self.bars

        # skip first 20 days to get full windows
        print('LY: len(bars) is {}'.format(len(bars)))
        #print('LY: last bar is {}'.format(bars[-1]))
        #if len(bars) < 20:
            #return

        # compute averages using internal rolling_mean
        bars['short_ma'] = bars['close'].rolling_mean(window=10)
        bars['long_ma']  = bars['close'].rolling_mean(window=20)

        print('LY: short_ma is {}'.format(bars['short_ma'][-1]))
        print(bars.tail())

        # get current position data
        positions = instrument.get_positions()

        if not instrument.pending_orders and positions["position"] == 0:
            print('LY: instrument BUY every bar {}'.format(datetime.now()))
            instrument.buy(1)
            self.record(all_buy=1)

        if positions["position"] != 0:
            print('LY: instrument EXIT {}'.format(datetime.now()))
            instrument.exit()
            self.record(all_buy=-1)

        # trading logic - entry signal
        if bars['short_ma'].crossed_above(bars['long_ma'])[-1]:
            if not instrument.pending_orders and positions["position"] == 0:

                print('LY: instrument BUY {}'.format(datetime.now()))
                # buy one contract
                instrument.buy(1)

                print('LY: recording ma_cross=1')
                # record values for later analysis
                self.record(ma_cross=1)

        # trading logic - exit signal
        elif bars['short_ma'].crossed_below(bars['long_ma'])[-1]:
            if positions["position"] != 0:

                print('LY: instrument EXIT {}'.format(datetime.now()))
                # exit / flatten position
                instrument.exit()

                # record values for later analysis
                print('LY: recording ma_cross=-1')
                self.record(ma_cross=-1)


if __name__ == "__main__":
    symbol = "ES"
    symbol = "CL"
    print('Getting ready to run: {}'.format(symbol))
    print('Getting active contract')
    #ACTIVE_MONTH = futures.get_active_contract(symbol)
    #print("Active month for {} is: {}".format(symbol, ACTIVE_MONTH))

    ib_tuple = futures.make_tuple(symbol)
    print("Tuple is {}".format(ib_tuple))
    strategy = CrossOver(
        #instruments = [ (symbol, "FUT", "GLOBEX", "USD", ACTIVE_MONTH, 0.0, "") ], # ib tuples
        instruments = [ ib_tuple, ],
        resolution  = "1T", # Pandas resolution (use "K" for tick bars)
        bar_window  = 50, # no. of bars to keep
        #preload     = "3D", # Beyond 3D seem to hang
        #preload     = "1W", # preload 1 day history when starting, use tools.backdate
        preload     = "1D", # preload 1 day history when starting, use tools.backdate
        ibport    = 7497,        # IB port (7496/7497 = TWS, 4001 = IBGateway)
        blotter='MainBlotter',
    )
    print("LY: prerun")
    strategy.run()
    print('Finished')


    # Other arguments
    #ibport    = 4002,        # IB port (7496/7497 = TWS, 4001 = IBGateway)
    #timezone    = "US/Central", # convert all ticks/bars to this timezone
    #tick_window = 20, # no. of ticks to keep
