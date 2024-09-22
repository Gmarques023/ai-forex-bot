import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta

def round_time_to_previous_15_minutes(dt):
    dt = dt - timedelta(minutes=dt.minute % 15, seconds=dt.second, microseconds=dt.microsecond)
    return dt

def update_missing_data(symbol, csv_file):
    if not mt5.initialize():
        print("Failed to initialize MetaTrader 5")
        return
    
    try:
        existing_df = pd.read_csv(csv_file)
        existing_df['date'] = pd.to_datetime(existing_df['date']).dt.date
        existing_df['time_only'] = pd.to_datetime(existing_df['time_only'], format='%H:%M:%S').dt.time
        existing_df.set_index(['date', 'time_only'], inplace=True)
        print("Estrutura do CSV existente:")
        print(existing_df.tail())
        last_row = existing_df.iloc[-1]
        last_date = last_row.name[0]
        last_time = last_row.name[1]
        last_datetime = datetime.combine(last_date, last_time)
        print("Última data e hora no CSV:")
        print("Date:", last_date)
        print("Time:", last_time)
    except FileNotFoundError:
        existing_df = pd.DataFrame(columns=['date', 'time_only', 'open', 'high', 'low', 'close', 'tick_volume'])
        existing_df.set_index(['date', 'time_only'], inplace=True)
        last_datetime = datetime.now() - timedelta(days=1) 
        print("Ficheiro CSV não encontrado. A criar um novo DataFrame.")

    current_time = datetime.now() + timedelta(hours=2)
    rounded_current_time = round_time_to_previous_15_minutes(current_time)
    print("Última vela fechada: ", rounded_current_time)

    minutes_diff = int((rounded_current_time - last_datetime).total_seconds() // 60)
    num_bars = minutes_diff // 15
    
    print("Número de velas M15 em falta:", num_bars)
    if num_bars > 0:
        rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M15, last_datetime, rounded_current_time)
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
        df_new.set_index(['date', 'time_only'], inplace=True)
        df_new[['open', 'high', 'low', 'close']] = df_new[['open', 'high', 'low', 'close']].round(5)

        print("Novas velas obtidas:")
        print(df_new.tail())

        existing_df = pd.concat([existing_df, df_new])
        existing_df.to_csv(csv_file)
        
        print("CSV atualizado com sucesso.")
        print(existing_df.tail())
    else:
        print("Não há novas velas para atualizar.")

    mt5.shutdown()

update_missing_data('GBPUSD', '../data/GBPUSD/GBPUSD15.csv')

