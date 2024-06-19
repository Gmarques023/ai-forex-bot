#Script para avaliar a performance do modelo
import pandas as pd
import joblib
from sklearn.metrics import mean_squared_error

def evaluate_model(file_path, model_path):
    df = pd.read_csv(file_path, index_col='Date', parse_dates=True)
    
    # Define features and target
    X = df[['Open', 'High', 'Low', 'Close', 'Volume']]
    y = df['Close'].shift(-1).dropna()
    X = X[:-1]
    
    # Load the model
    model = joblib.load(model_path)
    
    # Make predictions
    y_pred = model.predict(X)
    
    # Calculate MSE
    mse = mean_squared_error(y, y_pred)
    print(f'Mean Squared Error: {mse}')

if __name__ == "__main__":
    evaluate_model('../data/processed/forex_data_processed.csv', '../models/forex_model.pkl')
