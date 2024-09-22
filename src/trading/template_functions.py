import MetaTrader5 as mt5
import pandas as pd
import os
import time
from datetime import datetime
from dotenv import load_dotenv
from utils.update_last_candles import update_last_candles
import joblib

# Carregar variáveis de ambiente
load_dotenv()

# Detalhes da conta
account_number = os.getenv('ACCOUNT_NUMBER')
account_password = os.getenv('ACCOUNT_PASSWORD')
account_server = "FPMarketsLLC-Demo"

print(f"Account Number: {account_number}")
print(f"Account Server: {account_server}")

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

model = joblib.load('./models/random_forest_model.pkl')

def place_order(symbol, order_type):
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"{symbol} not found, cannot place order")
        return
    
    if not symbol_info.visible:
        print(f"{symbol} is not visible, trying to switch on")
        if not mt5.symbol_select(symbol, True):
            print(f"symbol_select({symbol}) failed, exit")
            return
    
    symbol_info = mt5.symbol_info(symbol) 
    if symbol_info is None:
        print(f"{symbol} is still not found after trying to select it")
        return

    if not symbol_info.visible:
        print(f"{symbol} is still not visible after trying to select it")
        return
    
    point = symbol_info.point
    price = mt5.symbol_info_tick(symbol).ask if order_type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(symbol).bid
    deviation = 20
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": 0.01,
        "type": order_type,
        "price": price,
        "sl": price - 100 * point if order_type == mt5.ORDER_TYPE_BUY else price + 100 * point,
        "tp": price + 100 * point if order_type == mt5.ORDER_TYPE_BUY else price - 100 * point,
        "deviation": deviation,
        "magic": 234000,
        "comment": "Python script order",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    print(f"Order send result: {result}")
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Order failed: {result.comment}")

def get_last_candle_data_from_csv(csv_file):
    try:
        df = pd.read_csv(csv_file)
        df['time_only'] = pd.to_datetime(df['time_only'], format='%H:%M:%S', errors='coerce')
        if len(df) < 2:
            print(f"Not enough data in {csv_file} to determine the last candle")
            return None
        last_candle = df.iloc[-2]
        return last_candle 
    except FileNotFoundError:
        print(f"File {csv_file} not found.")
        return None
    except pd.errors.EmptyDataError:
        print(f"File {csv_file} is empty.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
def get_features_from_candle(candle):
    features = candle[['open', 'high', 'low', 'close']].values.reshape(1, -1)
    return features

def live_trading(symbol, csv_file):
    # Obter a última vela
    last_candle = get_last_candle_data_from_csv(csv_file)
    if last_candle is not None:
        features = get_features_from_candle(last_candle)
        prediction = model.predict(features)
        
        if prediction == 1:  # Prever alta
            print("Modelo prevê alta, colocando ordem de compra.")
            place_order(symbol, mt5.ORDER_TYPE_BUY)
        elif prediction == 0:  # Prever baixa
            print("Modelo prevê baixa, colocando ordem de venda.")
            place_order(symbol, mt5.ORDER_TYPE_SELL)

def wait_until_next_interval():
    now = datetime.now()
    current_minute = now.minute
    wait_time = 0
    if current_minute % 15 != 0:
        next_interval_minute = (current_minute // 15 + 1) * 15
        if next_interval_minute == 60:
            next_interval_minute = 0
            next_interval_hour = (now.hour + 1) % 24
            next_interval_time = now.replace(hour=next_interval_hour, minute=next_interval_minute, second=0, microsecond=0)
        else:
            next_interval_time = now.replace(minute=next_interval_minute, second=0, microsecond=0)
        wait_time = (next_interval_time - now).total_seconds()
    else:
        wait_time = 0
    
    print(f"Esperar {wait_time} segundos para o próximo intervalo.")
    time.sleep(wait_time)

if __name__ == "__main__":
    if not initialize_mt5():
        exit()
    
    try:
        while True:
            update_last_candles('GBPUSD', './data/GBPUSD/GBPUSD15.csv')
            live_trading('GBPUSD', './data/GBPUSD/GBPUSD15.csv')
            wait_until_next_interval()
    except KeyboardInterrupt:
        print("Interrompido pelo utilizador.")
    finally:
        mt5.shutdown()
        print("MetaTrader 5 fechado.")

