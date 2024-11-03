import MetaTrader5 as mt5
import os
from datetime import datetime
from dotenv import load_dotenv
from utils.update_last_candles import update_last_candles
from utils.wait_until_next_interval import wait_until_next_interval
from trading.live_tradingv2 import live_trading 
#from trading.live_trading_lstm import live_trading_lstm
load_dotenv()

account_number = os.getenv('ACCOUNT_NUMBER')
account_password = os.getenv('ACCOUNT_PASSWORD')
account_server = "FPMarketsLLC-Demo"
#account_server = "FPMarketsLLC-Live"

def initialize_mt5():
    if not mt5.initialize(
        path="C:\\Program Files\\FPMarkets MT5 Terminal\\terminal64.exe",
        login=int(account_number),
        password=account_password,
        server=account_server
    ):
        print(f"MetaTrader 5 initialization failed, error code = {mt5.last_error()}")
        return False
    print("MetaTrader 5 initialized successfully.")
    return True

if __name__ == "__main__":
    if not initialize_mt5():
        exit()

    last_trade_time = datetime.min 

    
    try:
        while True:
            update_last_candles('GBPUSD', './data/GBPUSD/GBPUSD15.csv')
            last_trade_time = live_trading('GBPUSD', './data/GBPUSD/GBPUSD15.csv', last_trade_time)
            wait_until_next_interval()
    except KeyboardInterrupt:
        print("Interrompido pelo utilizador.")
    finally:
        mt5.shutdown()
        print("MetaTrader 5 fechado.")
