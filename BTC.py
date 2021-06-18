import time
import pyupbit
import datetime
import numpy as np

access = "WCuPxUwgVLcNzzvAG7o2vUrOkPqyH46DSUW8xmD8"  # 본인 값으로 변경
secret = "4OiySwvAAx9ciqG6Mwfjkbwn6glIUMjPbmTCpzDB"  # 본인 값으로 변경
coin_name = "KRW-BTC"  # 코인 이름
coin_name2 = "BTC"  # 코인이름

key_k = 0.1  # k값

best_k = 0.0  # 제일좋은 키값
best_ror = 1  # 제일좋은 수익률


def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]["close"] + (df.iloc[0]["high"] - df.iloc[0]["low"]) * k
    return target_price


def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time


def get_ma15(ticker):
    """15일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=15)
    # 210508 rolling 15-> 3
    ma15 = df["close"].rolling(3).mean().iloc[-1]
    return ma15


def get_balance(coin):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b["currency"] == coin:
            if b["balance"] is not None:
                return float(b["balance"])
            else:
                return 0


# best k 값
def get_ror(k):
    df = pyupbit.get_ohlcv(coin_name, count=30)  # 210508 30일간 ohlcv
    df["range"] = (df["high"] - df["low"]) * k
    df["target"] = df["open"] + df["range"].shift(1)

    fee = 0.0005
    df["ror"] = np.where(df["high"] > df["target"], df["close"] / df["target"] - fee, 1)
    # 누적수익률
    ror = df["ror"].cumprod()[-2]
    return ror


def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]


# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")
count = 0
program_count = 0  # 초기 자본금 파악을 위한 count210508


# 자동매매 시작
while True:
    ####################################################################
    if best_k == 0:
        for k in np.arange(0.1, 1.0, 0.1):
            ror = get_ror(k)
            # print("%.1f %f" % (k, ror))
            if ror > best_ror:
                best_k = k
                best_ror = ror

        key_k = best_k  # best_k로 key_k 변경
        print("best key : {0}".format(key_k))

        print("타겟 값 : {0}".format(get_target_price(coin_name, key_k)))
        print("MA15 값 : {0}".format(get_ma15(coin_name)))
    #####################################################################

    # count가 0이면 초기화 1이면 구매 2이면 1/2매도 3이면 전량 매도

    try:
        now = datetime.datetime.now()
        start_time = get_start_time("KRW-BTC")  # 시작시간
        end_time = start_time + datetime.timedelta(days=1)

        # 9:00 < 현재 < 8:59:50
        if start_time < now < end_time - datetime.timedelta(hours=2):
            target_price = get_target_price(coin_name, key_k)
            ma15 = get_ma15(coin_name)
            current_price = get_current_price(coin_name)

            # 처음 실행인 경우210508
            if program_count == 0:
                krw = int(get_balance("KRW") * 0.25)

            # 첫번째 구매->전량매수 ///
            if target_price < current_price and ma15 < current_price:
                # 첫번째 조건을 만족하고 count==0 => 마감날 전량 매도한 뒤 전량 현금 보유일때,
                if count == 0:
                    if krw > 5000 and (target_price * 1.01 >= current_price):
                        buy_result = upbit.buy_market_order(coin_name, krw * 0.9995)
                        buy_price = current_price  # 현재가격 즉, 매수한 가격
                        count = 1  # 처음 전량 매수인 경우

            # 전량매수 후, 매수 금액에서 5%상승시 1/2 매도
            if count == 1:
                btc = get_balance(coin_name2)
                if buy_price * 1.06 >= current_price > buy_price * 1.049:
                    sell_result = upbit.sell_market_order(coin_name, btc * 0.5)
                    count = 2

            # 매수 금액에서 5%의 1/2를 매도한 후 10%상승시 나머지 금액의 1/2매도
            if count == 2:
                btc = get_balance(coin_name2)
                if buy_price * 1.1 >= current_price > buy_price * 1.09:
                    sell_result = upbit.sell_market_order(coin_name, btc * 0.5)
                    print(sell_result)
                    count = 3

        else:
            btc = get_balance(coin_name2)
            if btc > 0.00008:
                sell_result = upbit.sell_market_order(coin_name, btc * 0.9995)
                print(sell_result)
                count = 0
                best_k = 0
        # 반복문이 끝날때 1씩 더해준다210508
        program_count = program_count + 1
        time.sleep(1)
    except Exception as e:
        print(e)
        time.sleep(1)
