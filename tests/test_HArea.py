import pytest
import pdb

from OandaAPI import OandaAPI
from HArea import HArea
from CandleList import CandleList

@pytest.fixture
def oanda_object():
    '''Returns an  oanda object'''

    oanda = OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                     instrument='GBP_USD',
                     granularity='D',
                     alignmentTimezone='Europe/London',
                     start='2014-01-01T22:00:00',
                     end='2019-03-15T22:00:00')

    return oanda

def test_number_bounces(oanda_object):
    '''
    Test function to set basic candle features based on price
    i.e. self.colour, upper_wick, etc...
    '''

    candle_list = oanda_object.fetch_candleset()

    close_prices = []
    datetimes = []
    for c in oanda_object.fetch_candleset():
        close_prices.append(c.closeAsk)
        datetimes.append(c.time)

    resist=HArea(price=1.71690,pips=100, instrument='GBP_USD', granularity='D')

    (bounces,outfile)=resist.number_bounces(datetimes=datetimes,
                                            prices=close_prices)

def test_last_time(oanda_object):

    oanda = OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                     instrument='NZD_CAD',
                     granularity='D',
                     alignmentTimezone='Europe/London',
                     start='2005-01-01T22:00:00',
                     end='2019-03-21T22:00:00')

    candle_list = oanda.fetch_candleset()

    cl = CandleList(candle_list, instrument='NZD_CAD', granularity='D')


    resist = HArea(price=0.92216, pips=50, instrument='NZD_CAD', granularity='D')

    resist.last_time(clist=cl, position='above')

def test_get_bounce_feats():

    oanda = OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                     instrument='CAD_JPY',
                     granularity='H12',
                     alignmentTimezone='Europe/London',
                     start='2015-12-03T22:00:00',
                     end='2015-12-16T10:00:00')

    candle_list = oanda.fetch_candleset()

    cl = CandleList(candle_list, instrument='CAD_JPY', granularity='H12')

    (model, outfile) = cl.fit_reg_line()

    direction = None
    if model.coef_[0, 0] > 0:
        direction = 'up'
    else:
        direction = 'down'

    resist = HArea(price=88.608, pips=20, instrument='CAAD_JPY', granularity='H12')
