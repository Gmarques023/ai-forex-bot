import pandas as pd

def update_csv_labels(csv_file):
    df = pd.read_csv(csv_file, header=None)
    df.columns = ['date', 'time_only', 'open', 'high', 'low', 'close', 'tick_volume']
    df.to_csv(csv_file, index=False)
    print("Estrutura do CSV atualizado:")
    print(df.head())


update_csv_labels('../data/GBPUSD/GBPUSD15.csv')
