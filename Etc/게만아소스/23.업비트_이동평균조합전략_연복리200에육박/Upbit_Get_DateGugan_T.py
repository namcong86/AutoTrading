#-*-coding:utf-8 -*-
'''

기간을 알기 위한 샘플 예
이 파이썬 파일 코딩 후 시간이 지났을 것이기 때문에
아래의 숫자들은 변경해서 사용하세요 ^^! 

관련 포스팅

연복리 200에 가까운 이평조합 전략!
https://blog.naver.com/zacra/223074617299

위 포스팅을 꼭 참고하세요!!!

하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고

주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739

그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^



'''

import pyupbit



coin_ticker = "KRW-BTC"

#1. 전체 기간
#df = pyupbit.get_ohlcv(coin_ticker,interval="day",count=6000, period=0.3)
#2. 상승장
#df = pyupbit.get_ohlcv(coin_ticker,interval="day",count=1150, period=0.3)
#3. 횡보장
#df = pyupbit.get_ohlcv(coin_ticker,interval="day",count=350, period=0.3)
#4. 하락장
df = pyupbit.get_ohlcv(coin_ticker,interval="day",count=570, period=0.3)


############# 이동평균선! ###############
df['30ma'] = df['close'].rolling(30).mean() #30일선까지 테스트할때 사용하니깐 이걸 정의 해줘야 아래 데이터 없는 항목이 있는 걸 날릴 때 동일하게 날려져서 같은 기간으로 시작 된다.
########################################

df.dropna(inplace=True) #데이터 없는건 날린다!


#1. 전체 기간
#df = df
#2. 상승장
#df = df[:len(df)-730]
#3. 횡보장
#df = df[:len(df)-35]
#4. 하락장
df = df[:len(df)-290]

print(df.iloc[21].name, " ~ ", df.iloc[-1].name) #구간분할과 비교하기 위해 21일 이후에 투자가 시작되는 걸 감안!

