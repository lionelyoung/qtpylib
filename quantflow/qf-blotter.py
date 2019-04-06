from qtpylib.blotter import Blotter
import configparser

class MainBlotter(Blotter):
    pass # we just need the name

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('qfconfig.ini')
    blotter = MainBlotter(
        dbhost    = config['quantflow']['dbhost'],
        dbname    = config['quantflow']['dbname'],
        dbuser    = config['quantflow']['dbuser'],
        dbpass    = config['quantflow']['dbpass'],
        ibport    = config['quantflow']['ibport'],
        orderbook = False         # fetch and stream order book data
    )

    blotter.run()
