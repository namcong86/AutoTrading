#-*-coding:utf-8 -*-
'''

관련 포스팅

https://blog.naver.com/zacra/223728753947


위 포스팅을 꼭 참고하세요!!!

하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고

주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739

그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^

  
'''
import json
from requests import  Session
import pprint

#코인을 저장할 리스트!!
Top100CoinList = list()

#파일 경로입니다.
#top100coin_file_path = "./Top100CoinList.json" #내 PC에서
top100coin_file_path = "/var/autobot/Top100CoinList.json" #서버에서

url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
parameters = {
    'start': '1',
    'limit': '100',  
    'convert': 'USD'
}
headers = {
    'Accepts': 'application/json',
    'X-CMC_PRO_API_KEY': '여러분의 API키'  # 여기에 본인의 API 키를 입력하세요
}

session = Session()
session.headers.update(headers)

try:
    response = session.get(url, params=parameters)
    data = json.loads(response.text)
    
    # 데이터 구조 확인을 위한 디버깅 출력
    print("데이터 구조:", type(data))
    if 'data' in data:
        print("첫 번째 코인 데이터:", data['data'][0] if data['data'] else "데이터 없음")
    
    # 모든 코인의 정보를 저장
    coins_list = []
    for coin in data['data']:
        pprint.pprint(coin)

        if isinstance(coin, dict) and 'symbol' in coin:
            coin_info = {
                'symbol': coin['symbol'],
                'tags': coin.get('tags', [])  # tags가 없는 경우 빈 리스트 반환
            }
            coins_list.append(coin_info)
    
    # 상위 100개만 선택
    top_100_coins = coins_list[:100]
    
    print("필터링된 코인:", top_100_coins)
    print(f'가져온 코인 수: {len(top_100_coins)}')

    # 파일에 저장
    with open(top100coin_file_path, 'w') as outfile:
        json.dump(top_100_coins, outfile, indent=4)
        
except Exception as e:
    print(f'에러 발생: {e}')
    # 에러 상세 정보 출력
    import traceback
    print(traceback.format_exc())

