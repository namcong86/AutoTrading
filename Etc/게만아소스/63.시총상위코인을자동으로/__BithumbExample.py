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
import myBithumb
import pprint

Top100CoinList = list()

#파일 경로입니다.
#top100coin_file_path = "./Top100CoinList.json" #내 PC에서
top100coin_file_path = "/var/autobot/Top100CoinList.json" #서버에서

try:
    #이 부분이 파일을 읽어서 리스트에 넣어주는 로직입니다. 
    with open(top100coin_file_path, 'r') as json_file:
        Top100CoinList = json.load(json_file)

except Exception as e:
    #처음에는 파일이 존재하지 않을테니깐 당연히 예외처리가 됩니다!
    print("Exception by First")


pprint.pprint(Top100CoinList)


# 'stablecoin' : 스테이블 코인, 'centralized-exchange' : 중앙화 거래소 코인
def GetTopCoinList(Top100CoinList, count, include_tags=['all'], exclude_tags=['none']):
    """
    시가총액 상위 코인들을 가져오되, 특정 태그를 포함하거나 제외하여 필터링합니다.
    
    Args:
        count (int): 가져올 코인의 개수
        include_tags (list): 포함할 태그 리스트 (기본값: ['all'] - 모든 태그 포함)
        exclude_tags (list): 제외할 태그 리스트 (기본값: ['none'])
    
    Returns:
        list: 필터링된 코인 심볼 리스트
    """
    
    filtered_coins = []
    
    for coin_info in Top100CoinList:
        # include_tags가 'all'이 아닌 경우, 포함할 태그 확인
        if 'all' not in include_tags:
            if not any(tag in coin_info['tags'] for tag in include_tags):
                continue
        
        # exclude_tags는 include_tags에 명시적으로 요청된 태그는 제외하지 않음
        if any(tag in coin_info['tags'] for tag in exclude_tags) and not any(tag in include_tags for tag in coin_info['tags']):
            continue
                
        filtered_coins.append(coin_info['symbol'])
        
        if len(filtered_coins) >= count:
            break
            
    return filtered_coins


def GetTopMarketCapCoinList(TopCoinList, count):
    """
    시가총액 상위 코인 중 업비트에 상장된 코인만 필터링하여 반환
    :param count: 원하는 코인 개수
    :return: 필터링된 코인 리스트
    """
    BithumbCoinList = myBithumb.GetTickers()

    bithumb_coins = set(coin.replace("KRW-", "") for coin in BithumbCoinList)
    filtered_coins = []
    
    for coin in TopCoinList:
        if coin in bithumb_coins:
            filtered_coins.append(f"KRW-{coin}")
        if len(filtered_coins) >= count:
            break
            
    return filtered_coins



# 상위 20개 코인을 가져오되 스테이블 코인과 거래소 코인은 제외합니다
print("#########################################################")
print("시총 상위 20개 코인을 가져오되 스테이블 코인과 거래소 코인은 제외합니다")
ResultList = GetTopCoinList(Top100CoinList, 20,['all'],['stablecoin','centralized-exchange'])
print(ResultList)
for idx, coin in enumerate(ResultList, 1):
    print(f"{idx}위: {coin}")
print("#########################################################\n")


# 빗썸 상장된 상위 10개 코인을 가져옵니다.
print("#########################################################")
print("빗썸에 상장된 상위 10개 코인을 가져옵니다.")
UpbitCoinTopList = GetTopMarketCapCoinList(ResultList, 10)
print(UpbitCoinTopList)
for idx, coin in enumerate(UpbitCoinTopList, 1):
    print(f"{idx}위: {coin}")

print("#########################################################")

