import telegram
import asyncio
import inspect
import os

# 각 오토봇에 대한 토큰과 채팅 ID 설정 (수정 필요)
# 파일명의 첫 '.' 까지의 문자열을 키로 사용 (예: "1", "2", "3", "3-2", "3-3")
BOT_CONFIGS = {
    "0": {"token": "7256112961:AAEiErEbMWAlsSzjU_3sYkippfjId8gl71o", "chat_id": "785579073"},  # 0.JAN_TOTAL
    "1": {"token": "7884521715:AAGCgZ5qEmrGjgWmHfJAFDJBb5osxSWx4CA", "chat_id": "785579073"},  # 1.Upbit_Safe_BTC_Spot.py
    "2": {"token": "8171304113:AAEAHXACEXfmee026mRelw3r07vFiyqbQ5o", "chat_id": "785579073"},  # 2.Binance_F_BTC_Leverage
    "3": {"token": "8175142086:AAEGcKyOutXeM6b0RJVlrASznhsNGYrQRj4", "chat_id": "785579073"},  # 3.Binance_F_DOGE_PEPE_Leverage
    "3-2": {"token": "8402500792:AAFT8DJr_-lsWgcIkPLyYsXui2VhMGWodAo", "chat_id": "785579073"},  # 3-2.GateIO_F_DOGE_PEPE_Leverage
    "3-3": {"token": "8033456685:AAGg_V7oqzxsC2TYpU1wEbTNAyqDgqMBlQ4", "chat_id": "785579073"},  # 3-3.Bitget_F_DOGE_PEPE_Leverage
    "4": {"token": "8028505122:AAF0xB3J2aWFN8QSGRLzBsplJQ7ugaHaqbg", "chat_id": "785579073"},  # 4.GateIO_F_Grid_Danta
    "5": {"token": "7003568385:AAHI6CRDnXFTUWVdCmuwgB8JB7_Y2t_YRuo", "chat_id": "785579073"},  # 5.Bitget_F_Long_Short_Alt
    "6": {"token": "8276010783:AAHfyHb93OZqLjhENspxX17_3jCOX7lpL1k", "chat_id": "785579073"},  # 6.Kosdaqpi_Bot
    "7": {"token": "8226724190:AAF5CdEHf6T2SHZQ87mKv2Skis-OCRJIL_g", "chat_id": "785579073"},  # 7.Us_BothSide_3X_Strategy_Bot
    "8": {"token": "8228219079:AAEkZI0F69uPlfCWLxaJFXUM4cwZIpOemsk", "chat_id": "785579073"},  # 8.Snow_Kr_Bot
    "9": {"token": "8543401239:AAGWz-UHsU6hggpgAWTVdY18zhDo4W4viO8", "chat_id": "785579073"},  # 9.MA_Strategy_Bot
    
}

async def send_telegram_alert(bot, chat_id, msg):
    await bot.send_message(chat_id=chat_id, text=msg)

def SendMessage(msg):
    try:
        # 호출 스택에서 첫 번째 호출자 파일명 추출
        caller_frame = inspect.stack()[1]
        caller_file = caller_frame.filename
        caller_name = os.path.basename(caller_file)  # 파일명 추출 (예: 3-2.GateIO_F_DOGE_PEPE_Leverage.py)
        
        # 첫 '.' 까지의 문자열을 추출 (예: "1", "3", "3-2", "3-3")
        if '.' in caller_name:
            bot_key = caller_name.split('.')[0]  # 첫 '.' 기준으로 분리하여 앞부분 추출
        else:
            bot_key = caller_name[0]  # '.'이 없으면 첫 글자만 사용

        # BOT_CONFIGS에서 해당 키로 설정 가져오기
        if bot_key in BOT_CONFIGS:
            config = BOT_CONFIGS[bot_key]
            bot = telegram.Bot(token=config["token"])
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(send_telegram_alert(bot, config["chat_id"], msg))
            else:
                loop.run_until_complete(send_telegram_alert(bot, config["chat_id"], msg))
        else:
            raise ValueError(f"No configuration found for file key '{bot_key}'.")
    except Exception as ex:
        print(f"Error: {ex}")

# 필요 시 테스트용
if __name__ == "__main__":
    SendMessage("Test message from main")