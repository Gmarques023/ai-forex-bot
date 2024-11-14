import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
import os

def round_time_to_previous_15_minutes(dt):
    return dt - timedelta(minutes=dt.minute % 15, seconds=dt.second, microseconds=dt.microsecond)

def update_last_candles(symbol, csv_file):
    # Conectar ao MetaTrader 5
    if not mt5.initialize():
        print("Erro ao inicializar o MetaTrader 5")
        return
    
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


# update_last_candles("GBPUSD", "../data/GBPUSD/GBPUSD15.csv")


