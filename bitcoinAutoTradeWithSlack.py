import time
import pyupbit
import datetime
import requests

access = "WCuPxUwgVLcNzzvAG7o2vUrOkPqyH46DSUW8xmD8"  # 본인 값으로 변경
secret = "4OiySwvAAx9ciqG6Mwfjkbwn6glIUMjPbmTCpzDB"  # 본인 값으로 변경
coin_name = "KRW-DOGE"  # 코인 이름
coin_name2 = "DOGE"  # 코인이름
key_k = 0.5  # k값
myToken = "xoxb-1995815147381-2005095539639-LrBQ3pjcAuFBCitQll0KkTlQ"


def post_message(token, channel, text):
    response = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer " + token},
        data={"channel": channel, "text": text},
    )
    print(response)


post_message(myToken, "#upbit", "코인 자동화 프로그램 시작!")


# def get_target_price(ticker, k):
#     # """변동성 돌파 전략으로 매수 목표가 조회"""
#     df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
#     # target_price = df.iloc[0]["close"] + (df.iloc[0]["high"] - df.iloc[0]["low"]) * k

#     # df["target"] = df["open"] + (df["open"] - (df["low"] + df["high"]) / 2) * key_k

#     # 시가에 (저가+고가)/2 한것을 시가에빼서 k값을 곱한값을 더한다
#     target_price = ((df.iloc[0]["low"] + df.iloc[0]["high"]) / 2) + (
#         df.iloc[0]["close"] - (df.iloc[0]["low"] + df.iloc[0]["high"]) / 2
#     ) * k
#     return target_price
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
    ma15 = df["close"].rolling(15).mean().iloc[-1]
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


def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]


# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")
count = 0

# 시작 메세지 슬랙 전송
post_message(myToken, "#upbit", "자동매매시작")


# 자동매매 시작
while True:
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
            # 첫번째 구매->전량매수 ///
            if target_price < current_price and ma15 < current_price:
                # 첫번째 조건을 만족하고 count==0 => 마감날 전량 매도한 뒤 전량 현금 보유일때,
                if count == 0:
                    krw = get_balance("KRW")
                    if krw > 5000:
                        buy_result = upbit.buy_market_order(coin_name, krw * 0.9995)

                        buy_price = current_price  # 현재가격 즉, 매수한 가격
                        post_message(
                            myToken, "#upbit", "BTC buy : " + str(buy_result)
                        )  # Slack 봇
                        print(buy_result)
                        count = 1  # 처음 전량 매수인 경우

            # 전량매수 후, 매수 금액에서 5%상승시 1/2 매도
            if count == 1:
                btc = get_balance(coin_name2)
                if buy_price * 1.06 >= current_price > buy_price * 1.04:
                    sell_result = upbit.sell_market_order(coin_name, btc * 0.5)
                    post_message(myToken, "#upbit", "BTC buy : " + str(sell_result))
                    print(sell_result)
                    count = 2

            # 매수 금액에서 5%의 1/2를 매도한 후 10%상승시 나머지 금액의 1/2매도
            if count == 2:
                btc = get_balance(coin_name2)
                if buy_price * 1.1 >= current_price > buy_price * 1.09:
                    sell_result = upbit.sell_market_order(coin_name, btc * 0.5)
                    post_message(myToken, "#upbit", "BTC buy : " + str(sell_result))
                    print(sell_result)
                    count = 3

        else:
            btc = get_balance(coin_name2)
            if btc > 0.00008:
                sell_result = upbit.sell_market_order(coin_name, btc * 0.9995)
                post_message(myToken, "#upbit", "BTC buy : " + str(sell_result))
                print(sell_result)
                count = 0
        time.sleep(1)
    except Exception as e:
        print(e)
        time.sleep(1)
