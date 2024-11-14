import MetaTrader5 as mt5
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime, timedelta
import time
import joblib
import numpy as np
import pandas_ta as ta

load_dotenv()

account_number = os.getenv('ACCOUNT_NUMBER')
account_password = os.getenv('ACCOUNT_PASSWORD')
account_server = "FPMarketsLLC-Demo"
#account_server = "FPMarketsLLC-Live"

# Carregar o modelo treinado
model_path = './models/trained_models/random_time_series.pkl'
model = joblib.load(model_path)

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

# Função para atualizar as últimas velas no CSV
def round_time_to_previous_15_minutes(dt):
    return dt - timedelta(minutes=dt.minute % 15, seconds=dt.second, microseconds=dt.microsecond)

def update_last_candles(symbol, csv_file):
    try:
        # Carregar apenas a última linha do CSV para obter a data e hora mais recentes
        last_row = pd.read_csv(csv_file, usecols=['date', 'time_only']).iloc[-1]
        last_datetime = datetime.strptime(f"{last_row['date']} {last_row['time_only']}", "%Y-%m-%d %H:%M:%S")
    except (FileNotFoundError, IndexError):
        # Definir uma data inicial caso o CSV não exista ou esteja vazio
        last_datetime = datetime.now() - timedelta(days=1)
        print("Ficheiro CSV não encontrado ou vazio. A iniciar uma nova base de dados.")

    current_time = datetime.now() + timedelta(hours=3)
    rounded_current_time = round_time_to_previous_15_minutes(current_time)

    # Calcular o número de velas de 15 minutos a serem copiadas
    minutes_diff = int((rounded_current_time - last_datetime).total_seconds() // 60)
    num_bars = minutes_diff // 15

    if num_bars > 0:
        # Obter as velas que faltam desde a última registrada
        rates = mt5.copy_rates_from(symbol, mt5.TIMEFRAME_M15, rounded_current_time, num_bars)
        if rates is None:
            print(f"Erro ao obter as taxas para {symbol}")
            mt5.shutdown()
            return
        
        # Criar DataFrame com as novas velas
        df_new = pd.DataFrame(rates)
        df_new.columns = ['time', 'open', 'high', 'low', 'close', 'tick_volume', 'spread', 'real_volume']
        df_new['time'] = pd.to_datetime(df_new['time'], unit='s').dt.floor('min')
        df_new['date'] = df_new['time'].dt.date
        df_new['time_only'] = df_new['time'].dt.time

        # Selecionar e formatar colunas necessárias
        df_new = df_new[['date', 'time_only', 'open', 'high', 'low', 'close', 'tick_volume']]
        df_new = df_new.round({'open': 5, 'high': 5, 'low': 5, 'close': 5})

        # Carregar e concatenar apenas as velas novas ao CSV
        df_existing = pd.read_csv(csv_file) if os.path.exists(csv_file) else pd.DataFrame()
        df_existing = pd.concat([df_existing, df_new]).drop_duplicates(subset=['date', 'time_only'], keep='last')
        df_existing.to_csv(csv_file, index=False)
        
        print("CSV atualizado com sucesso.")
    else:
        print("Nenhuma vela nova para atualizar.")

def get_last_candle_data_from_csv(csv_file):
    try:
        df = pd.read_csv(csv_file)
        df['time_only'] = pd.to_datetime(df['time_only'], format='%H:%M:%S', errors='coerce')
        if len(df) < 1:
            print(f"Not enough data in {csv_file} to determine the last candle")
            return None
        last_candle = df.iloc[-1]
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
        #"sl": price - 10000 * point if order_type == mt5.ORDER_TYPE_BUY else price + 100 * point,
        #"tp": price + 10000 * point if order_type == mt5.ORDER_TYPE_BUY else price - 100 * point,
        "deviation": deviation,
        "magic": 234000,
        "comment": "Python script order",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    #print(f"Order send result: {result}")
    print("")
    print("Ordem colocada")
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Order failed: {result.comment}")

# Função para criar janelas deslizantes com base nas últimas velas selecionadas
def create_rolling_window_features(data, window_size=60):
    if len(data) >= window_size:
        window = data.iloc[-window_size:].copy()

        # Calcular o RSI e a SMA
        window['RSI_10'] = ta.rsi(window['close'], length=10)
        window['SMA_200'] = ta.sma(window['close'], length=200)
        
        # Identificar se a vela é vermelha
        window['is_red'] = window['close'] < window['open']
        
        # Preencher valores NaN gerados pelo RSI e SMA com o último valor válido
        window['RSI_10'] = window['RSI_10'].ffill()
        window['SMA_200'] = window['SMA_200'].ffill()
        
        # Garantir que não haja NaNs restantes (caso a janela seja pequena para SMA)
        window = window.bfill()
        
        # Selecionar as features desejadas e achatar os dados
        features = window[['open', 'high', 'low', 'close', 'volume', 'RSI_10', 'SMA_200', 'is_red']].values.flatten()
        return np.array([features])
    
    return np.array([])

def live_trading(symbol, csv_file, last_trade_time):
  
    df = pd.read_csv(csv_file)
    
    # Renomear colunas
    df.columns = ['date', 'time_only', 'open', 'high', 'low', 'close', 'volume']
    df['date'] = pd.to_datetime(df['date'])
    df['hour'] = pd.to_datetime(df['time_only'], format='%H:%M:%S').dt.hour
    
    # Obter a última vela
    last_candle = get_last_candle_data_from_csv(csv_file)

    if last_candle is not None:
        candle_time = pd.to_datetime(f"{last_candle['date']} {last_candle['time_only']}")
        candle_time = candle_time.replace(tzinfo=None)
        last_trade_time = last_trade_time.replace(tzinfo=None)

        # Executar a previsão para a nova vela
        if candle_time > last_trade_time:
            rolling_features = create_rolling_window_features(df.iloc[:-1], window_size=60)
            
            if rolling_features.size > 0:
                # Print das features da vela atual
                #print(f"Features da vela atual (últimas 60 velas):")
                #print(rolling_features)

                prediction_proba = model.predict_proba(rolling_features)[0]
                print(f"Probabilidade de 3 velas vermelhas: {prediction_proba[1]:.2f}")

                previous_features = create_rolling_window_features(df.iloc[:-2], window_size=60)
                if previous_features.size > 0:
                    # Print das features da vela anterior
                    #print(f"Features da vela anterior (últimas 60 velas):")
                    #print(previous_features)

                    previous_prediction_proba = model.predict_proba(previous_features)[0]
                    print(f"Probabilidade de 3 velas vermelhas consecutivas na vela anterior: {previous_prediction_proba[1]:.2f}")
                    
                    # Condição para Sell (3 velas vermelhas consecutivas previstas)
                    if prediction_proba[1] > 0.01: #and previous_prediction_proba[1] < 0.5:
                        previous_candle = df.iloc[-1]
                        print("Alta probabilidade de 3 velas vermelhas consecutivas, colocando ordem de venda.")
                        place_order(symbol, mt5.ORDER_TYPE_SELL)
                        
                        # Atualizar o last_trade_time somente após realizar a negociação
                        last_trade_time = candle_time
                      
                else:
                    print("Não foi possível calcular a previsão para a vela anterior.")
            return last_trade_time
        else:
            print("Já foi feita uma negociação para esta vela.")
    return last_trade_time

def wait_until_next_interval():
    now = datetime.now()
    current_minute = now.minute
    wait_time = 0
    next_interval_minute = (current_minute // 15 + 1) * 15

    # Corrige o caso em que next_interval_minute chega a 60
    if next_interval_minute == 60:
        next_interval_minute = 0
        next_interval_hour = (now.hour + 1) % 24
        next_interval_time = now.replace(hour=next_interval_hour, minute=next_interval_minute, second=1, microsecond=0)
    else:
        next_interval_time = now.replace(minute=next_interval_minute, second=1, microsecond=0)

    # Calcula o tempo de espera e garante que é positivo
    wait_time = max((next_interval_time - now).total_seconds(), 0.1)
    time.sleep(wait_time)
  
if __name__ == "__main__":
    if not initialize_mt5():
        exit()

    last_trade_time = datetime.min 
   
    try:
        while True:
            update_last_candles('GBPUSD', './data/GBPUSD/GBPUSD.csv')
            last_trade_time = live_trading('GBPUSD', './data/GBPUSD/GBPUSD.csv', last_trade_time)
            wait_until_next_interval()
    except KeyboardInterrupt:
        print("Interrompido pelo utilizador.")
    finally:
        mt5.shutdown()
        print("MetaTrader 5 fechado.")
