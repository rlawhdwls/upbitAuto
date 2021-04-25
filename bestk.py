import pyupbit
import numpy as np

coin_name = "KRW-BTT" #코인 이름
coin_name2="RFR" #코인이름
key_k=0.3 #k값

# best k 값
def get_ror(k=0.5):
    df = pyupbit.get_ohlcv(coin_name,count=7)
    df['range'] = (df['high'] - df['low']) * k
    df['target'] = df['open'] + df['range'].shift(1)

    fee = 0.0005
    df['ror'] = np.where(df['high'] > df['target'],
                         df['close'] / df['target'] - fee,
                         1)
    # 누적수익률
    ror = df['ror'].cumprod()[-2]
    return ror


for k in np.arange(0.1, 1.0, 0.1):
    ror = get_ror(k)
    print("%.1f %f" % (k, ror))







