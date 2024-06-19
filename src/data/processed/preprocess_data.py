import pandas as pd
from sklearn.preprocessing import MinMaxScaler

def preprocess_data(file_path):
    df = pd.read_csv(file_path, index_col='Date', parse_dates=True)
    df = df.dropna()
    
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(df)
    scaled_df = pd.DataFrame(scaled_data, index=df.index, columns=df.columns)
    
    # Save processed data
    scaled_df.to_csv('../data/processed/forex_data_processed.csv')
    return scaled_df

if __name__ == "__main__":
    preprocess_data('../data/raw/forex_data.csv')
