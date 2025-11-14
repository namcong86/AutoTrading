#-*-coding:utf-8 -*-
'''

기간을 알기 위한 샘플 예
이 파이썬 파일 코딩 후 시간이 지났을 것이기 때문에
아래의 숫자들은 변경해서 사용하세요 ^^! 


관련 포스팅

연복리 25%의 코스닥 지수 양방향 매매 전략!
https://blog.naver.com/zacra/223078498415
위 포스팅을 꼭 참고하세요!!!

하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고

주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739

그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^



'''


import KIS_Common as Common
import KIS_API_Helper_KR as KisKR

import pandas as pd
import pprint


#계좌 선택.. "VIRTUAL" 는 모의 계좌!
Common.SetChangeMode("VIRTUAL") #REAL or VIRTUAL




coin_ticker = "233740" #KODEX 코스닥150레버리지
#1. 전체 기간
df = Common.GetOhlcv("KR",coin_ticker, 1645)
#2. 상승장
#df = Common.GetOhlcv("KR",coin_ticker, 1630)
#3. 횡보장
#df = Common.GetOhlcv("KR",coin_ticker, 610)
#4. 하락장
#df = Common.GetOhlcv("KR",coin_ticker, 380)


############# 이동평균선! ###############
df['30ma'] = df['close'].rolling(30).mean() #30일선까지 테스트할때 사용하니깐 이걸 정의 해줘야 아래 데이터 없는 항목이 있는 걸 날릴 때 동일하게 날려져서 같은 기간으로 시작 된다.
########################################

df.dropna(inplace=True) #데이터 없는건 날린다!


#1. 전체 기간
#df = df
#2. 상승장
#df = df[:len(df)-1290]
#3. 횡보장
#df = df[:len(df)-320]
#4. 하락장
#df = df[:len(df)-130]

print(df.iloc[1].name, " ~ ", df.iloc[-1].name) 

