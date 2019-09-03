from pivotlist  import PivotList
from oanda_api import OandaAPI
from candlelist import CandleList

import pytest
import pdb


@pytest.fixture
def pl_object():
    '''Returns PivotList object'''

    oanda = OandaAPI(url='https://api-fxtrade.oanda.com/v1/candles?',
                     instrument='AUD_USD',
                     granularity='D',
                     alignmentTimezone='Europe/London',
                     dailyAlignment=22)

    oanda.run(start='2018-01-25T22:00:00',
              end='2018-10-12T22:00:00',
              roll=True)

    candle_list = oanda.fetch_candleset()

    cl = CandleList(candle_list, instrument='AUD_USD', type='long')

    pl = cl.get_pivotlist(outfile='test.png', th_up=0.02, th_down=-0.02)

    return pl

def test_merge_segments(pl_object):
    '''Test merge_segments method'''

    slist=pl_object.slist

    slist.merge_segments()

   # assert pl.slist[0].count==35
