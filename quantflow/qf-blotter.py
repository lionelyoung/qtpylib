from qtpylib.blotter import Blotter
import configparser
import os
import sys
BASE_DIR = os.path.dirname(os.path.realpath(__file__))

class MainBlotter(Blotter):
    pass # we just need the name

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read(os.path.join(BASE_DIR, 'qfconfig.ini'))
    blotter = MainBlotter(
        dbhost    = config['quantflow']['dbhost'],
        dbname    = config['quantflow']['dbname'],
        dbuser    = config['quantflow']['dbuser'],
        dbpass    = config['quantflow']['dbpass'],
        ibport    = config['quantflow']['ibport'],
        orderbook = False         # fetch and stream order book data
    )

    blotter.run()
