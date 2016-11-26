# -*- coding: utf-8 -*-
import _pickle as pkl
import numpy as np
import os
import pandas as pd

def get_symbol(symbol, data_loc, start_date=None, end_date=None):
    pickle_file = data_loc+symbol+'.pkl'
    if os.path.isfile(pickle_file):
        print("Reading", symbol, "from pickle")
        df = pd.read_pickle(pickle_file)
    else:
        try:
            df = pd.read_csv(
                data_loc+symbol+'.txt', dtype={'Time': object}
            )
        except:
            print("failed to read in ",symbol)
            return None
    if not os.path.isfile(pickle_file):
        df['timestamp'] = pd.to_datetime(
            df['Date']+" "+ df['Time'], format="%m/%d/%Y %H%M"
        )
        df.set_index('timestamp', drop=False, inplace=True)
        df.drop(['Date', 'Time'], axis=1, inplace=True)
        pkl.dump(df, open(pickle_file, 'wb'), protocol=2)
        print("Dumped ", symbol, " to pickle")
    
    if start_date and end_date:
        return df[( (df['timestamp'] >= pd.to_datetime(start_date)) \
                  & (df['timestamp'] <= pd.to_datetime(end_date)))]
    else:
        return df

def df_to_returns(df, price='Close'):
    prices = df[price]
    prices_shifted = np.roll(prices, -1)
    rets = (prices_shifted-prices)  / prices_shifted
    return rets[:len(rets)-1]

def get_symbols_matrix(symbols, data_loc, start_date, end_date, price='Close'):
    df = pd.DataFrame(columns=symbols) 
    real_syms = []
    for s in symbols:
        sym = get_symbol(s, data_loc, start_date, end_date)
        if (check_integrity(sym)):
            df[s] = df_to_returns(sym)
            real_syms.append(sym)
        else:
            df.drop(s, axis=1, inplace=True)
            print(s, "failed integrity check")
    df.fillna(method='ffill', axis=1, inplace=True)
    return df, real_syms

# Creates a data frame where each row is a window of the series with future returns 
def get_windows_rets(df, window_length=60, window_offset=10, forward=(1,2,5,10)):
    return 1

def check_integrity(sym):
    # A good way to check for full data in a trading day
    is_full = (sym.groupby(sym.timestamp.dt.date).count() > 380).all()
    return is_full.all()
