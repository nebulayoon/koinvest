from datetime import datetime, timedelta
import json
import time
import requests

from config import config


APP_KEY = config.APP_KEY
APP_SECRET = config.APP_SECRET
URL_BASE = config.URL_BASE


# (2) 함수 정의
## 1. 접근 토큰 발급
def get_access_token():
    """OAuth 인증 > 접근토큰발급"""
    headers = {"content-type": "application/json"}
    body = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
    }
    PATH = "oauth2/tokenP"
    URL = f"{URL_BASE}/{PATH}"

    time.sleep(0.1)  # 유량제한 예방 (REST: 1초당 20건 제한)
    res = requests.post(URL, headers=headers, data=json.dumps(body))

    if res.status_code == 200:
        try:
            access_token = res.json().get("access_token")
            access_token_expired = res.json().get("access_token_expired")  # 수정된 키
            return access_token, access_token_expired
        except KeyError as e:
            print(f"토큰 발급 중 키 에러 발생: {e}")
            print(res.json())
            return None, None
    else:
        print("접근 토큰 발급이 불가능합니다. 응답 코드:", res.status_code)
        print("응답 내용:", res.json())
        return None, None


## 2. 해외 주식 분봉 조회
def call_api(exc_code, sym_code, nmin, keyb="", next_value="", access_token=""):
    PATH = "/uapi/overseas-price/v1/quotations/inquire-time-itemchartprice"
    URL = f"{URL_BASE}/{PATH}"

    params = {
        "AUTH": "",
        "EXCD": exc_code,  # 거래소 코드
        "SYMB": sym_code,  # 종목 코드
        "NMIN": nmin,  # 분봉 주기
        "PINC": "1",
        "NEXT": next_value,
        "NREC": "120",
        "FILL": "",
        "KEYB": keyb,
    }

    print(params)

    headers = {
        "content-type": "application/json",
        "authorization": f"Bearer {access_token}",  # 매개변수로 받은 access_token 사용
        "appkey": APP_KEY,  # 미리 정의된 appkey 사용
        "appsecret": APP_SECRET,  # 미리 정의된 appsecret 사용
        "tr_id": "HHDFS76950200",
        "custtype": "P",
    }

    time.sleep(0.1)  # 유량제한 예방 (REST: 1초당 20건 제한)
    response = requests.get(URL, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        print("API 호출 성공")
        return data
    else:
        print(f"API 호출 실패, 상태 코드: {response.status_code}")
        try:
            print("오류 메시지:", response.json())
        except json.JSONDecodeError:
            print("JSON 디코딩 실패. 응답:", response.text)
        return None


## 2. 해외 주식 분봉 조회
def call_exchange_api(access_token=""):
    PATH = "/uapi/overseas-price/v1/quotations/inquire-time-indexchartprice"
    URL = f"{URL_BASE}/{PATH}"

    params = {
        "FID_COND_MRKT_DIV_CODE": "N",
        "FID_INPUT_ISCD": "SPX",
        "FID_HOUR_CLS_CODE": "0",
        "FID_PW_DATA_INCU_YN": "Y",
    }

    print(params)

    headers = {
        "content-type": "application/json",
        "authorization": f"Bearer {access_token}",  # 매개변수로 받은 access_token 사용
        "appkey": APP_KEY,  # 미리 정의된 appkey 사용
        "appsecret": APP_SECRET,  # 미리 정의된 appsecret 사용
        "tr_id": "FHKST03030200",
        "custtype": "P",
    }

    time.sleep(0.1)  # 유량제한 예방 (REST: 1초당 20건 제한)
    response = requests.get(URL, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        print("API 호출 성공")
        return data
    else:
        print(f"API 호출 실패, 상태 코드: {response.status_code}")
        try:
            print("오류 메시지:", response.json())
        except json.JSONDecodeError:
            print("JSON 디코딩 실패. 응답:", response.text)
        return None


## 3. 다음 조회용 keyb 값 계산 함수 (nmin에 따라 시간 조정)
def get_next_keyb(output2, nmin):
    last_record = output2[-1]
    last_time_str = (
        last_record["xymd"] + last_record["xhms"]
    )  # YYYYMMDDHHMMSS 형태의 문자열
    last_time = datetime.strptime(
        last_time_str, "%Y%m%d%H%M%S"
    )  # 문자열을 datetime 객체로 변환
    next_keyb_time = last_time - timedelta(minutes=nmin)  # nmin 값만큼 이전 시간 계산
    return next_keyb_time.strftime("%Y%m%d%H%M%S")  # 다시 문자열로 변환하여 반환


def fetch_and_save_data(exc_code, sym_code, nmin, period, access_token):
    first_call = call_api(exc_code, sym_code, nmin, access_token=access_token)

    if not first_call:
        return

    print(first_call)

    # 다음 조회를 위한 변수 초기화
    next_value = first_call["output1"]["next"]
    keyb = get_next_keyb(
        first_call["output2"], nmin
    )  # nmin에 따라 1분 또는 n분 전 시간 계산

    for _ in range(period - 1):
        print("=" * 50)
        # 다음 조회 실행
        next_call = call_api(
            exc_code,
            sym_code,
            nmin,
            keyb=keyb,
            next_value=next_value,
            access_token=access_token,
        )

        if not next_call:
            break

        print(next_call)
        # 다음 조회를 위한 keyb 및 next 값 갱신
        next_value = next_call["output1"]["next"]
        keyb = get_next_keyb(next_call["output2"], nmin)  # nmin에 따라 갱신된 keyb 값


# (4) 함수 실행
## 1. 접근토큰 발급
ACCESS_TOKEN, ACCESS_TOKEN_EXPIRED = get_access_token()

if ACCESS_TOKEN:
    ## 2. 사용자 입력 받기
    exc_code = input("거래소 코드를 입력하세요 (예: NAS): ")
    sym_code = input("종목 코드를 입력하세요 (예: TSLA): ")
    nmin = int(input("분봉 주기를 입력하세요 (예: 1, 5, 10): "))
    period = int(input("반복 조회할 횟수를 입력하세요 (예: 4): "))

    # fetch_and_save_data(exc_code, sym_code, nmin, period, ACCESS_TOKEN)

    print(call_exchange_api(ACCESS_TOKEN))

else:
    print("토큰 발급 실패로 프로그램이 종료됩니다.")
