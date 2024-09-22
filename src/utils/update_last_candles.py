import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta

def round_time_to_previous_15_minutes(dt):
    dt = dt - timedelta(minutes=dt.minute % 15, seconds=dt.second, microseconds=dt.microsecond)
    return dt

def update_last_candles(symbol, csv_file):
    # Conectar ao MetaTrader 5
    if not mt5.initialize():
        print("Failed to initialize MetaTrader 5")
        return
    
    try:
        existing_df = pd.read_csv(csv_file)
        existing_df['date'] = pd.to_datetime(existing_df['date']).dt.date
        existing_df['time_only'] = pd.to_datetime(existing_df['time_only'], format='%H:%M:%S').dt.time
        existing_df.set_index(['date', 'time_only'], inplace=True)
        last_row = existing_df.iloc[-1]
        last_date = last_row.name[0]
        last_time = last_row.name[1]
        last_datetime = datetime.combine(last_date, last_time)
    except FileNotFoundError:
        existing_df = pd.DataFrame(columns=['date', 'time_only', 'open', 'high', 'low', 'close', 'tick_volume'])
        existing_df.set_index(['date', 'time_only'], inplace=True)
        last_datetime = datetime.now() - timedelta(days=1) 
        print("Ficheiro CSV não encontrado. A criar um novo DataFrame.")

    current_time = datetime.now() + timedelta(hours=3)
    rounded_current_time = round_time_to_previous_15_minutes(current_time)

    minutes_diff = int((rounded_current_time - last_datetime).total_seconds() // 60)
    
    num_bars = minutes_diff // 15

    if num_bars > 0:
        rates = mt5.copy_rates_from(symbol, mt5.TIMEFRAME_M15, rounded_current_time - timedelta(minutes=15), num_bars)
        if rates is None:
            print(f"Failed to get rates for {symbol}")
            mt5.shutdown()
            return
    
        df_new = pd.DataFrame(rates)
        df_new.columns = ['time', 'open', 'high', 'low', 'close', 'tick_volume', 'spread', 'real_volume']
        df_new['time'] = pd.to_datetime(df_new['time'], unit='s').dt.floor('min')
        df_new['date'] = df_new['time'].dt.date
        df_new['time_only'] = df_new['time'].dt.time

        df_new = df_new[['date', 'time_only', 'open', 'high', 'low', 'close', 'tick_volume']]
        df_new = df_new.round({'open': 5, 'high': 5, 'low': 5, 'close': 5})
        df_new.set_index(['date', 'time_only'], inplace=True)

        existing_df = pd.concat([existing_df, df_new])
        existing_df = existing_df[~existing_df.index.duplicated(keep='last')]
        existing_df.to_csv(csv_file)
            
        print("CSV atualizado com sucesso.")
    else:
        print("Não há novas velas para atualizar.")



#update_last_candles("GBPUSD", "../data/GBPUSD/GBPUSD15.csv")


