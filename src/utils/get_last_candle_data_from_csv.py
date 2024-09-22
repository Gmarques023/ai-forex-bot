import pandas as pd

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