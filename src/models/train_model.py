#Script para treinar o modelo de machine learning
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

def train_model(file_path):
    df = pd.read_csv(file_path, index_col='Date', parse_dates=True)
    
    # Define features and target
    X = df[['Open', 'High', 'Low', 'Close', 'Volume']]
    y = df['Close'].shift(-1).dropna()
    X = X[:-1]
    
    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    
    # Train the model
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    # Evaluate the model
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    print(f'Mean Squared Error: {mse}')
    
    # Save the model
    import joblib
    joblib.dump(model, '../models/forex_model.pkl')

if __name__ == "__main__":
    train_model('../data/processed/forex_data_processed.csv')
