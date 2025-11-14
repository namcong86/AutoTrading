'''

관련 포스팅

트레이딩뷰 웹훅 알림 받아 주식 자동매매 봇 완성하기 
https://blog.naver.com/zacra/223050088124

위 포스팅을 꼭 참고하세요!!!

하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고

주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739

그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^


'''
import line_alert
import json
import sys

import KIS_Common as Common
import KIS_API_Helper_KR as KisKR
import KIS_API_Helper_US as KisUS


#######################################################################
#######################################################################

# https://youtu.be/GmR4-AiJjPE 여기를 참고하세요 트레이딩뷰 웹훅 관련 코드입니다!

#######################################################################
#######################################################################

data = json.loads(sys.argv[1])

print(data)


line_alert.SendMessage("Data GET!: " + str(data) + "\n Logic Start!!")

# account -> 'VIRTUAL' or 'REAL' or .....등의 계좌명
# area -> 'US' or 'KR' 어떤 지역인지
# stock_code -> "SPY" ,"005930" 등의 종목코드
# type -> "limit" 지정가매매, "market" 시장가매매
# side -> "buy"는 매수, "sell"은 매도
# price -> 지정가 매매"limit"의 경우에 진입가격
# amt -> 매수/매도할 수량


#{"account":"VIRTUAL","area":"US","stock_code":"SPY","type":"limit","side":"sell","price":370.0,"amt":1}

Common.SetChangeMode(data['account']) #계좌 세팅!

#한국일 경우!
if data['area'] == "KR":
    print("KR")

    if data['type'] == "market":

        if data['side'] == "buy":
            KisKR.MakeBuyMarketOrder(data['stock_code'],data['amt'])

        elif data['side'] == "sell":
            KisKR.MakeSellMarketOrder(data['stock_code'],data['amt'])

    elif data['type'] == "limit":
        
        if data['side'] == "buy":
            KisKR.MakeBuyLimitOrder(data['stock_code'],data['amt'],data['price'])

        elif data['side'] == "sell":

            KisKR.MakeSellLimitOrder(data['stock_code'],data['amt'],data['price'])


#US 즉 미국일 경우
else:
    print("US")

    if data['type'] == "market":

        #현재가!
        CurrentPrice = KisUS.GetCurrentPrice(data['stock_code'])

        if data['side'] == "buy":

            #현재가보다 위에 매수 주문을 넣음으로써 시장가로 매수
            CurrentPrice *= 1.01
            KisUS.MakeBuyLimitOrder(data['stock_code'],data['amt'],CurrentPrice)


        elif data['side'] == "sell":

            #현재가보다 아래에 매도 주문을 넣음으로써 시장가로 매도
            CurrentPrice *= 0.99
            KisUS.MakeSellLimitOrder(data['stock_code'],data['amt'],CurrentPrice)

    elif data['type'] == "limit":

        if data['side'] == "buy":
            KisUS.MakeBuyLimitOrder(data['stock_code'],data['amt'],data['price'])

        elif data['side'] == "sell":

            KisUS.MakeSellLimitOrder(data['stock_code'],data['amt'],data['price'])



line_alert.SendMessage("Logic Done!!")







