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
        is_full, bad_days = check_integrity(sym)
        if (is_full):
            df[s] = df_to_returns(sym)
            real_syms.append(sym)
        else:
            df.drop(s, axis=1, inplace=True)
            print(s, "failed integrity check")
    df.fillna(method='ffill', axis=1, inplace=True)
    return df, real_syms

# Creates a data frame where each row is a window of the series with future returns 
def get_windows_rets(sym, window_length=60, window_offset=1, forward=(1,2,5,10), price='Close'):
    days = sym.groupby([sym.index.year, sym.index.month, sym.index.day])
    mf = max(forward)
    n_windows = int( (388 - window_length-mf) / window_offset )
    windows = np.zeros( (len(days)*n_windows, window_length) ) 
    rets = np.zeros( (len(days)*n_windows, len(forward)))
    di = 0
    invalid_days = [] 
    for d, day in days:
        if (len(day) > 388):
            pday = df_to_returns(day)
            for wi in range(n_windows):
                ei = wi*window_offset+window_length
                windows[di*n_windows + wi, :] = pday[wi*window_offset:ei]
                frets = (1+pday[ei+1:ei+mf+1]).cumprod() - 1
                for fi in range(len(forward)):
                    rets[di*n_windows+wi, fi] = frets[forward[fi]-1] 
            di += 1
        else:
            invalid_days.append(d)
    print(invalid_days)
    return windows[:di*n_windows], rets[:di*n_windows] 

def get_volume_windows(sym, window_length=60, window_offset=1):
    days = sym.groupby([sym.index.year, sym.index.month, sym.index.day])
    n_windows = int( (388 - window_length-2) / window_offset )
    windows = np.zeros( (len(days)*n_windows, window_length) ) 
    di = 0
    invalid_days = []
    for d, day in days:
        if (len(day) > 388):
            vols = day['Volume'].values
            for wi in range(n_windows):
                ei = wi*window_offset+window_length
                windows[di*n_windows + wi, :] = vols[wi*window_offset:ei]
            di += 1
        else:
            invalid_days.append(d)
    return windows[:di*n_windows]

def check_integrity(sym):
    # A good way to check for full data in a trading day
    bad_data = sym.groupby(sym.timestamp.dt.date).count() > 370
    bad_days = bad_data.Close
    is_full = bad_days.all()
    return is_full, bad_days
