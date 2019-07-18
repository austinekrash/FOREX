import datetime


PROJECT = {
    'root' :'/Users/ernesto/projects/FOREX/CTDBTP/'
}

OANDA_API = {
    'url': 'https://api-fxtrade.oanda.com/v1/candles?',
    'alignmentTimezone' : 'Europe/London',
    'dailyAlignment': 22

}

#configuration for Counter doubletop
CTDBT = {
    'period' : 2000, # number of candles from self.start that will be considered in order to
                     # to look for peaks/valleys
    'HR_pips' : 100, # number of pips over/below S/R used for trying to identify bounces
    'step_pips': 5, # number of pips to increase HR_pips in order to widen the area to look for bounces
    'max_HRpips' : 500, # max number of pips that will be used in order to widen the area to look for bounces
    'min_dist' : 5, # Minimum distance between peaks
    'period1st_bounce' : 5, # Controls the maximum number of candles allowed between
                           # self.start and this 'period1st_bounce' in order look for the 1st bounce
    'period2nd_bounce': 75,  # Controls the maximum number of candles allowed between
                             # datetime controlled by 'period1st_bounce' and datetime controlled by 'period2nd_bounce'
                             # in order to detect the 2nd bounce
    'period_trend': 500, # Controls the maximum number of candles before self.bounce_2nd in order to look for start
                         # of trend
    'HR_pips_from2nd': 60,  # The same than before but restricted to bounces found from 2nd bounce (not including it)
    'threshold_from2nd': 0.5,  # idem
    'min_dist_from2nd': 5,  # idem
}

# start datetime for Oanda's historical data
START_HIST = {
    'AUD_CAD': datetime.datetime(2004, 6, 5, 21, 0),
    'AUD_JPY': datetime.datetime(2004, 6, 5, 21, 0),
    'AUD_NZD': datetime.datetime(2004, 6, 5, 21, 0),
    'AUD_USD': datetime.datetime(2002, 6, 5, 21, 0),
    'CAD_JPY': datetime.datetime(2004, 6, 5, 21, 0),
    'EUR_AUD': datetime.datetime(2004, 6, 5, 21, 0),
    'EUR_CAD': datetime.datetime(2004, 6, 5, 21, 0),
    'EUR_CHF': datetime.datetime(2002, 6, 5, 21, 0),
    'EUR_GBP': datetime.datetime(2002, 6, 5, 21, 0),
    'EUR_JPY': datetime.datetime(2002, 6, 5, 21, 0),
    'EUR_USD': datetime.datetime(2002, 6, 5, 21, 0),
    'GBP_AUD': datetime.datetime(2004, 6, 5, 21, 0),
    'GBP_JPY': datetime.datetime(2002, 6, 5, 21, 0),
    'GBP_USD': datetime.datetime(2002, 6, 5, 21, 0),
    'NZD_CAD': datetime.datetime(2004, 6, 1, 21, 0),
    'NZD_JPY': datetime.datetime(2004, 6, 1, 21, 0),
    'NZD_USD': datetime.datetime(2002, 9, 5, 21, 0),
    'USD_CAD': datetime.datetime(2002, 6, 5, 21, 0),
    'USD_CHF': datetime.datetime(2002, 6, 5, 21, 0),
    'USD_JPY': datetime.datetime(2002, 6, 5, 21, 0),
    'AUD_CHF': datetime.datetime(2004, 6, 5, 21, 0),
}

PNGFILES = {
    'fig_sizes' : (20, 10), # tuple controlling the size of figures
    'regression' : PROJECT['root']+'regresion_imgs/',
    'bounces' : PROJECT['root']+'bounce_images/',
    'init_trend' : PROJECT['root']+'init_trend_imgs/'
}
