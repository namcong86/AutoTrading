import telegram
import asyncio
import inspect
import os

# 각 오토봇에 대한 토큰과 채팅 ID 설정 (수정 필요)
BOT_CONFIGS = {
    "0": {"token": "7256112961:AAEiErEbMWAlsSzjU_3sYkippfjId8gl71o", "chat_id": "785579073"},  # 0.JAN_TOTAL
    "1": {"token": "7884521715:AAGCgZ5qEmrGjgWmHfJAFDJBb5osxSWx4CA", "chat_id": "785579073"},  # 1.Upbit_Safe_BTC_Spot.py
    "2": {"token": "8171304113:AAEAHXACEXfmee026mRelw3r07vFiyqbQ5o", "chat_id": "785579073"},  # 2.Binance_F_BTC_Leverage
    "3": {"token": "8175142086:AAEGcKyOutXeM6b0RJVlrASznhsNGYrQRj4", "chat_id": "785579073"},  # 3.Binance_F_DOGE_PEPE_Leverage + 3.GateIO_F_DOGE_PEPE_Leverage
    "4": {"token": "8028505122:AAF0xB3J2aWFN8QSGRLzBsplJQ7ugaHaqbg", "chat_id": "785579073"},  # 4.GateIO_F_Grid_Danta
    
}

async def send_telegram_alert(bot, chat_id, msg):
    await bot.send_message(chat_id=chat_id, text=msg)

def SendMessage(msg):
    try:
        # 호출 스택에서 첫 번째 호출자 파일명 추출
        caller_frame = inspect.stack()[1]
        caller_file = caller_frame.filename
        caller_name = os.path.basename(caller_file)  # 파일명 추출 (예: Upbit_Safe_BTC_Spot.py)
        first_char = caller_name[0]  # 파일명의 첫 글자 추출 (예: "1")

        # BOT_CONFIGS에서 해당 키로 설정 가져오기
        if first_char in BOT_CONFIGS:
            config = BOT_CONFIGS[first_char]
            bot = telegram.Bot(token=config["token"])
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(send_telegram_alert(bot, config["chat_id"], msg))
            else:
                loop.run_until_complete(send_telegram_alert(bot, config["chat_id"], msg))
        else:
            raise ValueError(f"No configuration found for file starting with '{first_char}'.")
    except Exception as ex:
        print(f"Error: {ex}")

# 필요 시 테스트용
if __name__ == "__main__":
    SendMessage("Test message from main")