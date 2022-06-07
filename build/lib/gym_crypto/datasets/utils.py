import multiprocessing
import os

from numba import jit
import numpy as np
import pandas as pd
import talib


manager = multiprocessing.Manager()
norm_arrays = manager.dict()

# region constants
ADOSC_FAST = 24
ADOSC_SLOW = 45

ATR_PERIOD = 24

BB_PERIOD = 20
BB_STD_DEV_UP = 2
BB_STD_DEV_DOWN = 2

MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

MFI_PERIOD = 30

RSI_PERIOD = 14

DF_COLUMNS = [
    'open',
    'close',
    'high',
    'low',
    'volume',
    'adosc',
    'atr',
    'macd',
    'macd_signal',
    'macd_hist',
    'mfi',
    'upper_band',
    'middle_band',
    'lower_band',
    'rsi',
    'difference_low_high',
    'difference_open_close',
]
DF_COLUMNS_1 = [
    'open',
    'close',
    'high',
    'low',
    'volume',
    'adosc',
    'atr',
    'macd',
    'macd_signal',
    'macd_hist',
    'upper_band',
    'middle_band',
    'lower_band',
]
DF_COLUMNS_2 = ['mfi', 'rsi']
DF_COLUMNS_3 = ['difference_low_high', 'difference_open_close']
# endregion


@jit
def load_dataset(name):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, 'data', name + '.csv')
    df = pd.read_csv(path, parse_dates=True, engine="numba")

    # data checks
    df.fillna(0, inplace=True, engine="numba")
    df.replace([np.inf, -np.inf], 0, inplace=True, engine="numba")
    df = calc_indicators(df)

    return df


def calc_indicators(df):
    closes = df['close'].to_numpy(dtype=np.double)
    highs = df['high'].to_numpy(dtype=np.double)
    lows = df['low'].to_numpy(dtype=np.double)
    opens = df['open'].to_numpy(dtype=np.double)
    volumes = df['volume'].to_numpy(dtype=np.double)
    difference_low_high = np.divide(np.subtract(highs, lows), lows)
    difference_open_close = np.divide(np.subtract(closes, opens), opens)

    rsi = talib.RSI(closes, timeperiod=RSI_PERIOD)
    mfi = talib.MFI(highs, lows, closes, volumes, timeperiod=MFI_PERIOD)
    upperband, middleband, lowerband = talib.BBANDS(
        closes, timeperiod=BB_PERIOD, nbdevup=BB_STD_DEV_UP, nbdevdn=BB_STD_DEV_DOWN, matype=0
    )
    macd, macdsignal, macdhist = talib.MACD(
        closes, fastperiod=MACD_FAST, slowperiod=MACD_SLOW, signalperiod=MACD_SIGNAL
    )
    adosc = talib.ADOSC(highs, lows, closes, volumes, fastperiod=ADOSC_FAST, slowperiod=ADOSC_SLOW)
    atr = talib.ATR(highs, lows, closes, timeperiod=ATR_PERIOD)
    data1 = np.column_stack(
        (opens, closes, highs, lows, volumes, adosc, atr, macd, macdsignal, macdhist, upperband, middleband, lowerband)
    )
    data2 = np.column_stack((mfi, rsi))
    data3 = np.column_stack((difference_low_high, difference_open_close))
    df1 = pd.DataFrame(data1, columns=DF_COLUMNS_1)
    df2 = pd.DataFrame(data2, columns=DF_COLUMNS_2)
    df3 = pd.DataFrame(data3, columns=DF_COLUMNS_3)
    df1 = df1.iloc[-500:, :]
    df2 = df2.iloc[-500:, :]
    df3 = df3.iloc[-500:, :]

    df1 = df1.reset_index(drop=True)
    df2 = df2.reset_index(drop=True)
    df3 = df3.reset_index(drop=True)

    df = multi_normalize(df1, df2, df3)

    return df


def multi_normalize(df1, df2, df3):
    norm_workers = []
    for col in df1.columns:
        p = multiprocessing.Process(
            target=normalize,
            args=(
                df1[f"{col}"],
                col,
            ),
        )
        p.start()
        # time.sleep(3)
        norm_workers.append(p)

    for col in df2.columns:
        p = multiprocessing.Process(
            target=normalize,
            args=(
                df2[f"{col}"],
                col,
            ),
        )
        p.start()
        norm_workers.append(p)
    for p in norm_workers:
        p.join()
    data1 = np.column_stack(
        (
            norm_arrays["open"],
            norm_arrays["close"],
            norm_arrays["high"],
            norm_arrays["low"],
            norm_arrays["volume"],
            norm_arrays["adosc"],
            norm_arrays["atr"],
            norm_arrays["macd"],
            norm_arrays["macd_signal"],
            norm_arrays["macd_hist"],
            norm_arrays["upper_band"],
            norm_arrays["middle_band"],
            norm_arrays["lower_band"],
        )
    )
    data2 = np.column_stack((norm_arrays["mfi"], norm_arrays["rsi"]))

    df1 = pd.DataFrame(data1, columns=DF_COLUMNS_1)
    df2 = pd.DataFrame(data2, columns=DF_COLUMNS_2)

    df = pd.concat([df1, df2], axis=1)
    df = pd.concat([df, df3], axis=1)
    df.reset_index(drop=True, inplace=True)
    df.replace([np.inf, -np.inf], 0, inplace=True)
    df.fillna(0, inplace=True)
    df = df.reindex(columns=DF_COLUMNS)

    return df


def normalize(df, row):
    df_new = np.ndarray(shape=df.shape, dtype=np.double)
    df.fillna(0, inplace=True)

    for i in range(len(df)):
        if i != 0:
            df[i - 1] = 0 if (np.isnan(df[i - 1]) or df[i - 1] == np.inf or df[i - 1] == -np.inf) else df[i - 1]
            df_new[i] = (df[i] - df[i - 1]) / df[i - 1]

    norm_arrays[row] = df_new
