# -*- coding: utf-8 -*-
'''

python -m pip install --upgrade pykrx
python install --upgrade pykrx
python3 install --upgrade pykrx 

관련 포스팅
https://blog.naver.com/zacra/223548787076

위 포스팅을 꼭 참고하세요!!!

하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고

주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739

그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^


'''
import KIS_Common as Common
import KIS_API_Helper_KR as KisKR
import json
import line_alert
import time

from pykrx import stock

Common.SetChangeMode("VIRTUAL")

#스팩주는 코스닥에 있다. 코스닥 종목 다 가져옴
kosdaq_list = stock.get_market_ticker_list(market="KOSDAQ")

print(len(kosdaq_list))

result = "스팩주 종목 코드 수집"
print(result)
line_alert.SendMessage(result)
    
SpacList = list()
for ticker in kosdaq_list:
    name = stock.get_market_ticker_name(ticker)
    time.sleep(0.2)
    if "스팩" in name:
        SpacList.append(ticker)
        print(name,ticker)
    print("..")
        
        
#파일 경로입니다.
file_path = "/var/autobot/SPAC_TickerList.json"
#파일에 리스트를 저장합니다
with open(file_path, 'w') as outfile:
    json.dump(SpacList, outfile)


result = "스팩주 종목 코드 수집 끝"
print(result)
line_alert.SendMessage(result)
