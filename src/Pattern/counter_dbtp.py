import pdb
import warnings

import matplotlib
from Pattern.counter import Counter
from oanda_api import OandaAPI

matplotlib.use('PS')
import matplotlib.pyplot as plt
import datetime
import config
import numpy as np
from utils import *
from candlelist import CandleList
from harea import HArea

class CounterDbTp(Counter):
    '''
    This class represents a trade showing Counter doubletop pattern (inherits from Counter)

    Class variables
    ---------------

    id : str, Required
         Id used for this object
    start: datetime, Required
           Time/date when the trade was taken. i.e. 20-03-2017 08:20:00s
    pair: str, Required
          Currency pair used in the trade. i.e. AUD_USD
    timeframe: str, Required
               Timeframe used for the trade. Possible values are: D,H12,H10,H8,H4
    entry: float, Optional
           entry price
    trend_i: datetime, Required
             start of the trend
    type: str, Optional
          What is the type of the trade (long,short)
    SL:  float, Optional
         Stop/Loss price
    TP:  float, Optional
         Take profit price
    SR:  float, Optional
         Support/Resistance area
    bounce_1st : Candle object
                 For 1st bounce
    bounce_2nd : Candle object
                 For 2nd bounce
    bounces : list of Candle objects
              Containing the Candles occurring after the 2nd bounce
    rsi_1st : bool, Optional
              Is price in overbought/oversold
              area in first peak
    rsi_2nd : bool, Optional
              Is price in overbought/oversold
              area in second peak
    diff : int. Optional
            Variable containing the absolute (no sign) difference (in pips)
    diff_rsi : float. Optional
               Variable containing the difference between rsi_1st and rsi_2nd
    valley : int Optional
             Length in number of candles between  bounce_1st and bounce_2nd
    n_rsibounces : int, Optional
                  Number of rsi bounces for trend conducting to 2nd bounce
    rsibounces_lengths: list, Optional
                        List with lengths for each rsi bounce
    slope: float, Optional
           Float with the slope of trend conducting to 2nd bounce
    HR_pips: int, Optional
             Number of pips over/below S/R used for trying to identify bounces
             Default: 200
    threshold: float Optional
               Threshold for detecting peaks. Default : 0.50
    min_dist: int, Optional
              Minimum distance between peaks. Default : 5
    period: int, Optional
            number of candles from self.start that will be considered in order to
            to look for peaks/valleys
    period1st_bounce: int, Optional
                      Controls the maximum number of candles allowed from self.start
                      in order to locate the 1st bounce
                      Default:10
    period2nd_bounce: int, Optional
                      Controls the maximum number of candles allowed from
                      datetime of 1st bounce in order to locate the
                      2nd bounce. Default:10
    period_trend: int, Optional
                  Controls the maximum number of candles before self.bounce_2nd in order to look for start
                  of trend. Default: 300
    clist_period : CandleList
                   CandleList that goes from self.start to self.period.
                   It will be initialised by __initclist

    '''

    def __init__(self, pair, start, HR_pips=200, threshold=0.50, min_dist=5,
                 period1st_bounce=10, period2nd_bounce=10, period_trend=300, **kwargs):

        # get values from config file
        if 'HR_pips' in config.CTDBT: HR_pips = config.CTDBT['HR_pips']
        if 'threshold' in config.CTDBT: threshold = config.CTDBT['threshold']
        if 'min_dist' in config.CTDBT: min_dist = config.CTDBT['min_dist']
        if 'period1st_bounce' in config.CTDBT: period1st_bounce = config.CTDBT['period1st_bounce']
        if 'period2nd_bounce' in config.CTDBT: period2nd_bounce = config.CTDBT['period2nd_bounce']
        if 'period' in config.CTDBT: period = config.CTDBT['period']
        if 'period_trend' in config.CTDBT: period_trend = config.CTDBT['period_trend']

        self.pair = pair
        self.start = datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
        self.HR_pips = HR_pips
        self.threshold = threshold
        self.min_dist = min_dist
        self.period1st_bounce = period1st_bounce
        self.period2nd_bounce = period2nd_bounce
        self.period = period
        self.period_trend = period_trend

        allowed_keys = ['id', 'timeframe', 'entry', 'period', 'trend_i', 'type', 'SL',
                        'TP', 'SR', 'RR', 'lasttime']

        self.__dict__.update((k, v) for k, v in kwargs.items() if k in allowed_keys)

        # set TP
        if not hasattr(self, 'TP'):
            if not hasattr(self, 'RR'): raise Exception("Neither the RR not the TP is defined. Please provide RR")
            diff = (self.entry - self.SL) * self.RR
            self.TP = round(self.entry + diff, 4)

        # timepoint cutoff that the defines the period from which the first bounce needs to be
        # located
        self.__period1st_bounce_point = self.__get_time4candles(n=self.period1st_bounce,
                                                                anchor_point=self.start)

        # init the CandleList from self.period to self.start
        self.__initclist()
        # calc_rsi
        self.clist_period.calc_rsi()
        self.init_feats()

    def __get_time4candles(self, n, anchor_point,roll=True):
        '''
        This private function takes a a number of candles
        and returns a Datetime corresponding to
        this number of candles

        Parameters
        ----------
        n : int
            Number of candles
        anchor_point : datetime
            Datetime used as the anchor (end point from which it will go back 'n' candles) for calculation
        roll : boolean
               if True, then if will try to go back in time in order to get exactly 'n' number of candles.
               Default: True

        Returns
        -------
        Datetime.datetime
        '''

        delta_from_start = None
        delta_one = None
        if self.timeframe == "D":
            delta_from_start = datetime.timedelta(hours=24 * n)
            delta_one = datetime.timedelta(hours=24)
        else:
            fgran = self.timeframe.replace('H', '')
            delta_from_start = datetime.timedelta(hours=int(fgran) * n)
            delta_one = datetime.timedelta(hours=int(fgran))

        # calculate the cutoff for the first threshold using the number of candles
        oanda = OandaAPI(url=config.OANDA_API['url'],
                         instrument=self.pair,
                         granularity=self.timeframe,
                         alignmentTimezone=config.OANDA_API['alignmentTimezone'],
                         dailyAlignment=config.OANDA_API['dailyAlignment'])

        start = anchor_point - delta_from_start
        if roll is True:
            if start< config.START_HIST[self.pair]:
                #return the first candle in the record if start goes back before the start of the record
                return config.START_HIST[self.pair]
            else :
                end = anchor_point.isoformat()

                oanda.run(start=start.isoformat(),
                          end=end,
                          roll=True)

                candle_list = oanda.fetch_candleset()

                # if len of candle_list is below n then go back one candle at a time
                while len(candle_list) < n:
                        start = start - delta_one
                        oanda.run(start=start.isoformat(),
                                  end=end,
                                  roll=True)
                        candle_list = oanda.fetch_candleset()


                return start
        else:
            return start

    def __initclist(self):
        '''
        Private function to initialize the CandleList object that goes from self.start
        to self.period

        This will set the self.clist_period class attribute
        '''

        delta_period=periodToDelta(self.period, self.timeframe)
        delta_1=periodToDelta(1, self.timeframe)
        start = self.start - delta_period # get the start datetime for this CandleList period
        end = self.start + delta_1 # increase self.start by one candle to include self.start

        oanda = OandaAPI(url=config.OANDA_API['url'],
                         instrument=self.pair,
                         granularity=self.timeframe,
                         alignmentTimezone=config.OANDA_API['alignmentTimezone'],
                         dailyAlignment=config.OANDA_API['dailyAlignment'])

        oanda.run(start=start.isoformat(),
                  end=end.isoformat(),
                  roll=True
                  )

        candle_list = oanda.fetch_candleset(vol_cutoff=0)

        cl = CandleList(candle_list, self.pair, granularity=self.timeframe, id=self.id, type=self.type)

        self.clist_period=cl

    def __inarea_bounces(self, bounces, HRpips, part='closeAsk'):
        '''
        Function to identify the candles for which price is in the area defined
        by self.SR+HRpips and self.SR-HRpips

        Parameters
        ----------
        bounces: list
                 Containing the initial list of candles
        part: str
              Candle part used for the calculation. Default='closeAsk'

        Returns
        -------
        list with bounces that are in the area
        '''
        # get bounces in the horizontal area
        lower = substract_pips2price(self.pair, self.SR, HRpips)
        upper = add_pips2price(self.pair, self.SR, HRpips)

        in_area_list = []
        for c in bounces:
            price = getattr(c, part)
           # print("u:{0}-l:{1}|p:{2}|t:{3}".format(upper, lower, price,c.time))
            if price >= lower and price <= upper:
                in_area_list.append(c)

        return in_area_list

    def get_first_bounce(self, part='closeAsk'):
        '''
        Function that uses the the Zigzag algorithm to identify the first bounce (most recent)
        of the CounterDoubleTop pattern

        Parameters
        ----------
        part: str
              Candle part used for the calculation. Default='closeAsk'

        Returns
        -------
        It will set the self.bounce_1st attribute
        '''

        # get sliced CandleList from datetime defined by self.period1st_bounce period
        start_clist=self.clist_period.slice(start=self.__period1st_bounce_point)

        bounces=start_clist.get_pivots(th_up=0.00, th_down=-0.00)

        arr = np.array(start_clist.clist)

        # consider type of trade in order to select peaks or valleys
        if self.type=='short':
            bounce_candles = arr[bounces==1]
        elif self.type=='long':
            bounce_candles = arr[bounces==-1]

        in_area_list=self.__inarea_bounces(bounce_candles,part=part,HRpips=self.HR_pips)

        HRpips=self.HR_pips
        while len(in_area_list)==0 and HRpips<=config.CTDBT['max_HRpips']:
            HRpips=HRpips+config.CTDBT['step_pips']
            in_area_list = self.__inarea_bounces(bounce_candles, part=part, HRpips=HRpips)

        # keep running the improve_resolution function until a single bounce is obtained
        while len(in_area_list)>1:
            inarea_cl = CandleList(in_area_list, instrument=self.pair, granularity=self.timeframe)
            in_area_list=inarea_cl.improve_resolution(part=part,price=self.SR)

        assert len(in_area_list)==1, "Exactly one single bounce is needed"

        self.bounce_1st=in_area_list[0]

    def get_second_bounce(self, part='closeAsk'):
        '''
        Function that uses the the Zigzag algorithm to identify the second bounce
        of the CounterDoubleTop pattern

        Parameters
        ----------
        part: str
              Candle part used for the calculation. Default='closeAsk'

        Returns
        -------
        It will set the self.bounce_2nd attribute
        '''

        # timepoint cutoff that the defines the period from which the second bounce needs to be
        # located
        start = self.__get_time4candles(n=self.period2nd_bounce,
                                        anchor_point=self.bounce_1st.time)

        # get sliced CandleList from datetime defined by self.period1st_bounce period
        start_clist = self.clist_period.slice(start=start,end=self.bounce_1st.time)

        bounces = start_clist.get_pivots(th_up=0.00, th_down=-0.00)

        arr = np.array(start_clist.clist)

        # consider type of trade in order to select peaks or valleys
        if self.type == 'short':
            bounce_candles = arr[bounces == 1]
        elif self.type == 'long':
            bounce_candles = arr[bounces == -1]

        #if distance between 1st bounce and last detected bounce is less than 5 candles
        #then remove last detected bounce progressively
        diff=abs(self.bounce_1st.time-bounce_candles[-1].time)
        min_distDelta = periodToDelta(ncandles=15, timeframe=self.timeframe)
        while diff<=min_distDelta:
            bounce_candles=bounce_candles[:-1]
            diff = abs(self.bounce_1st.time - bounce_candles[-1].time)

        in_area_list = self.__inarea_bounces(bounce_candles, part=part, HRpips= self.HR_pips)

        HRpips = self.HR_pips
        while len(in_area_list) == 0 and HRpips <= config.CTDBT['max_HRpips']:
            HRpips = HRpips + config.CTDBT['step_pips']
            in_area_list = self.__inarea_bounces(bounce_candles, part=part, HRpips=HRpips)

        # keep running the improve_resolution function until a single bounce is obtained
        while len(in_area_list) > 1:
            inarea_cl = CandleList(in_area_list, instrument=self.pair, granularity=self.timeframe)
            in_area_list = inarea_cl.improve_resolution(part=part,price=self.SR)

        assert len(in_area_list) == 1, "Exactly one single bounce is needed"

        self.bounce_2nd = in_area_list[0]

    def get_restofbounces(self, part='closeAsk'):
        '''
        Function to get the rest of bounces. The ones occurring after the second bounce

        Parameters
        ----------
        part: str
              Candle part used for the calculation. Default='closeAsk'

        Returns
        -------
        It will set the bounces attribute
        '''

        # get sliced CandleList from datetime defined by self.period period
        start_clist = self.clist_period.slice(end=self.bounce_2nd.time)

        bounces = start_clist.get_pivots(th_up=0.01, th_down=-0.01)

        arr = np.array(start_clist.clist)

        # consider type of trade in order to select peaks or valleys
        if self.type == 'short':
            bounce_candles = arr[bounces == 1]
        elif self.type == 'long':
            bounce_candles = arr[bounces == -1]

        in_area_list = self.__inarea_bounces(bounce_candles, part=part, HRpips=self.HR_pips)

        self.bounces = in_area_list

    def plot_features(self, outfile, part='closeAsk'):
        '''
        Function to plot all bounces identified and also the start of the trend

        Parameters
        ----------
        outfile : filename for output
        '''

        prices = []
        datetimes = []
        for c in self.clist_period.clist:
            prices.append(getattr(c, part))
            datetimes.append(c.time)

        fig = plt.figure(figsize=config.PNGFILES['fig_sizes'])
        ax = plt.axes()
        ax.plot(datetimes, prices, color="black")

        #plotting the trend_i
        ix_trendi=datetimes.index(self.trend_i)
        plt.scatter(datetimes[ix_trendi], prices[ix_trendi], s=100, c="blue")

        final_bounces=self.bounces
        final_bounces.append(self.bounce_2nd)
        final_bounces.append(self.bounce_1st)
        for b in final_bounces:
            dt = b.time
            ix = datetimes.index(dt)
            plt.scatter(datetimes[ix], prices[ix], s=50)

        fig.savefig(outfile, format='png')

    def set_rsi_1st(self):
        '''
        Function to set rsi_1st class attribute

        Returns
        -------
        Nothing
        '''

        isonrsi = False
        if self.bounce_1st.rsi >= 70 or self.bounce_1st.rsi <= 30:
            isonrsi = True

        self.rsi_1st = isonrsi

    def set_rsi_2nd(self):
        '''
        Function to set rsi_2nd class attribute

        Returns
        -------
        Nothing
        '''

        isonrsi = False
        if self.bounce_2nd.rsi >= 70 or self.bounce_2nd.rsi <= 30:
            isonrsi = True

        self.rsi_2nd = isonrsi

    def init_feats(self):
        '''
        Function to initialise all object features

        Returns
        -------
        It will initialise all object's features
        '''

        warnings.warn("[INFO] Run init_feats")

        self.get_first_bounce(part='openAsk')
        self.get_second_bounce(part='openAsk')
        self.get_restofbounces(part='openAsk')
        self.set_rsi_1st()
        self.set_rsi_2nd()
        # if trend_i is not defined then calculate it
        if hasattr(self, 'trend_i'):
            self.trend_i = datetime.datetime.strptime(self.trend_i, '%Y-%m-%d %H:%M:%S')
        else:
            start = self.__get_time4candles(n=self.period_trend,
                                            anchor_point=self.bounce_2nd.time,
                                            roll=False)
            possible_clist_trend = self.clist_period.slice(start=start, end=self.bounce_2nd.time)
            startrend=possible_clist_trend.calc_itrend(th_up=0.05,th_down=-0.05)
            self.trend_i = startrend

        outfile = "{0}/{1}.final_bounces.png".format(config.PNGFILES['bounces'],
                                                     self.id.replace(' ', '_'))

        self.plot_features(outfile=outfile, part='openAsk')
        self.init_trend_feats()
        self.lasttime=self.clist_period.get_lasttime()
        self.set_entry_onrsi()
        self.bounces_fromlasttime()
        self.set_diff()
        self.set_diff_rsi()
        self.set_valley()
        self.set_rsibounces_feats()

        warnings.warn("[INFO] Done init_feats")

    def init_trend_feats(self):
        '''
        Function to initialize the features for
        trend going from 'trend_i' to 'bounce_2nd'

        Returns
        -------
        Nothing
        '''

        warnings.warn("[INFO] Run init_trend_feats")

        pdb.set_trace()

        self.set_slope()
        self.divergence = self.set_divergence()
        self.length_candles = c.length_candles
        self.length_pips = c.length_pips

        warnings.warn("[INFO] Done init_trend_feats")

    def bounces_fromlasttime(self):
        '''
        Function to get the bounces occurring after last_time

        Returns
        -------
        Will set the bounces_lasttime class attribute
        '''

        bounces = [n for n in self.bounces if n.time >= self.last_time]

        self.bounces_lasttime=bounces

    def set_entry_onrsi(self):
        '''
        Function to check if entry candle is on rsi territory (>=70 or <=30)

        Returns
        -------
        Will set the entry_onrsi class attribute
        '''

        entry_c=self.clist_period.fetch_by_time(self.start)

        isonrsi=False

        if entry_c.rsi>=70 or entry_c.rsi<=30:
            isonrsi=True

        self.entry_onrsi=isonrsi

    def set_diff(self):
        '''
        Function to calculate the diff between rsi_1st & rsi_2nd

        Returns
        -------
        It will set the 'diff' attribute of the class and calculate
        the number of pips from the difference. The sign will be ignored
        and the absolute number of pips is returned
        '''

        diff = self.bounce_1st.rsi - self.bounce_2nd.rsi
        (first, second) = self.pair.split("_")
        if first == 'JPY' or second == 'JPY':
            diff = diff * 100
        else:
            diff = diff * 10000

        self.diff = abs(round(diff))

    def set_diff_rsi(self):
        '''
        Function to calculate the diff between rsi_1st & rsi_2nd

        Returns
        -------
        It will set the 'diff_rsi' attribute of the class
        '''

        rsi1st_val = self.bounce_1st.rsi
        rsi2nd_val = self.bounce_2nd.rsi

        self.diff_rsi = rsi1st_val - rsi2nd_val

    def set_valley(self):
        '''
        Function to calculate the length of the valley
        between bounce_1st & bounce_2nd

        Returns
        -------
        It will set the 'valley' attribute of the class
        '''

        oanda = OandaAPI(url=config.OANDA_API['url'],
                         instrument=self.pair,
                         granularity=self.timeframe,
                         alignmentTimezone=config.OANDA_API['alignmentTimezone'],
                         dailyAlignment=config.OANDA_API['dailyAlignment'])

        oanda.run(start=self.bounce_2nd.time.isoformat(),
                  end=self.bounce_1st.time.isoformat())

        candle_list = oanda.fetch_candleset(vol_cutoff=0)

        self.valley = len(candle_list)

    def set_slope(self, k_perc=None):
        '''
        Function to set the slope for trend conducting to entry

        Parameters
        ----------
        k_perc : int
                 % of CandleList length that will be used as window size used for calculating the rolling average.
                 For example, if CandleList length = 20 Candles. Then the k=25% will be a window_size of 5
                 Default: None

         Returns
         -------
         Will set the slope class attribute and also the type attribute
         in self.clist_trend CandleList
         '''

        # first, lets create a CandleList for trend
        clist_trend = self.clist_period.slice(start=self.trend_i, end=self.bounce_2nd.time)

        if k_perc is not None:
            (model, outfile, mse) = clist_trend.fit_reg_line(k_perc=k_perc)
        else:
            (model, outfile, mse) = clist_trend.fit_reg_line()

        self.slope=model.coef_[0, 0]

        if model.coef_[0,0]>0:
            self.clist_trend.type='long'
        elif model.coef_[0,0]<0:
            self.clist_trend.type='short'

    def set_rsibounces_feats(self):
        '''
        Function to set the n_rsibounces and rsibounces_lengths
        for trend conducting to entry

        Returns
        -------
        Will set the n_rsibounces and rsibounces_lengths
        class attributes
        '''

        dict1 = self.clist_trend.calc_rsi_bounces()

        self.n_rsibounces = dict1['number']
        self.rsibounces_lengths = dict1['lengths']

    def set_divergence(self):
        '''
        Function to check if there is divergence involving the RSI indicator
        for trend conducting to entry

        Returns
        -------
        Will set the divergence class attribute
        '''

        # first, lets create a CandleList for trend
        clist_trend = self.clist_period.slice(start=self.trend_i, end=self.bounce_2nd.time)

        direction = None
        if self.slope > 0:
            direction = 'up'
        else:
            direction = 'down'

        res = clist_trend.check_if_divergence(direction=direction)

        self.divergence = res

