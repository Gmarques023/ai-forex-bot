import pandas as pd
import requests
from dotenv import load_dotenv
import os
from datetime import datetime

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

def fetch_data(pair='GBPUSD', interval='1min', outputsize='full', api_key=None):
    if not api_key:
        api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    base_url = "https://www.alphavantage.co/query"
    params = {
        "function": "FX_INTRADAY",
        "from_symbol": pair[:3],
        "to_symbol": pair[3:],
        "interval": interval,
        "apikey": api_key,
        "outputsize": outputsize
    }
    response = requests.get(base_url, params=params)
    data = response.json()
    
    if 'Time Series FX (1min)' not in data:
        print("Error fetching data from Alpha Vantage:", data)
        return None
    
    df = pd.DataFrame(data['Time Series FX (1min)']).T
    df.columns = ['Open', 'High', 'Low', 'Close']
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    return df

def merge_data(old_data_path, new_data):
    old_data = pd.read_csv(old_data_path, index_col='Date', parse_dates=True)
    merged_data = pd.concat([old_data, new_data])
    merged_data = merged_data[~merged_data.index.duplicated(keep='first')]
    return merged_data

if __name__ == "__main__":
    # Carregar dados antigos
    old_data_path = '../data/raw/GBPUSD_2004_2023.csv'  # Altere para o caminho do seu arquivo CSV
    old_data = pd.read_csv(old_data_path, index_col='Date', parse_dates=True)
    
    # Buscar dados recentes
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    recent_data = fetch_data(api_key=api_key)
    
    if recent_data is not None:
        # Filtrar dados para o período desejado
        start_date = '2024-06-17 00:00:00'
        end_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        filtered_recent_data = recent_data.loc[start_date:end_date]
        
        # Mesclar dados antigos e recentes
        merged_data = merge_data(old_data_path, filtered_recent_data)
        merged_data.to_csv('../data/processed/GBPUSD_M1_2004_2024.csv')
        
        specific_data = merged_data.loc['2004-01-01 00:00:00']
        print(specific_data)
