#-*-coding:utf-8 -*-
'''

관련 포스팅
https://blog.naver.com/zacra/223341020867

위 포스팅을 꼭 참고하세요!!!
 
하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고

주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739

그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^

'''
import myUpbit   #우리가 만든 함수들이 들어있는 모듈
import json


top_file_path = "/var/autobot/UpbitTopCoinList.json"

#거래대금이 많은 탑코인 30개의 리스트
TopCoinList = myUpbit.GetTopCoinList("day",30)

#파일에 리스트를 저장합니다
with open(top_file_path, 'w') as outfile:
    json.dump(TopCoinList, outfile)

