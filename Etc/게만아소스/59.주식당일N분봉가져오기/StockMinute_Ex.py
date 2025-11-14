# -*- coding: utf-8 -*-
'''

관련 포스팅
https://blog.naver.com/zacra/223571914494

위 포스팅을 꼭 참고하세요!!!

하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고

주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739

그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^


'''
import KIS_Common as Common
import KIS_API_Helper_KR as KisKR

import pprint

Common.SetChangeMode("VIRTUAL")

df = KisKR.GetOhlcvMinute("005930",'10T') # '1T','3T','5T','10T','15T','30T', '60T'
pprint.pprint(df)

print("---------------------\n")

ma = Common.GetMA(df,5,-1)
print("10분봉 현재 5이평선: ",ma)

rsi = Common.GetRSI(df,14,-1)
print("10분봉 현재 RSI14지표 : ",rsi)



    
