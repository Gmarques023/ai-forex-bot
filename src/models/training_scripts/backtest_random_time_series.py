import pandas as pd
import numpy as np
import joblib
import pandas_ta as ta

# Caminho para o modelo e para os dados do dia 7 de novembro
model_path = '../trained_models/random_time_series.pkl'
data_path = '../../data/GBPUSD/GBPUSD15.csv'

# Carregar o modelo treinado
model = joblib.load(model_path)

# Carregar os dados e filtrar para o dia 7 de novembro de 2024
df = pd.read_csv(data_path)
df.columns = ['date', 'time_only', 'open', 'high', 'low', 'close', 'volume']
df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time_only'])
df_nov7 = df[(df['datetime'] >= '2024-11-07') & (df['datetime'] < '2024-11-08')].copy()

# Calcular indicadores e features
df_nov7['SMA_200'] = ta.sma(df_nov7['close'], length=200)
df_nov7['RSI_10'] = ta.rsi(df_nov7['close'], length=10)
df_nov7['is_red'] = df_nov7['close'] < df_nov7['open']
df_nov7['Target_3_red'] = (df_nov7['is_red'].shift(0) & df_nov7['is_red'].shift(1) & df_nov7['is_red'].shift(2)).astype(int)

# Remover NaN iniciais gerados pelos indicadores
df_nov7.dropna(inplace=True)

# Função para criar janelas deslizantes de 60 velas
def create_rolling_window(data, window_size=60):
    rolling_data = []
    indices = []
    for i in range(window_size, len(data)):
        window = data.iloc[i-window_size:i][['open', 'high', 'low', 'close', 'volume', 'RSI_10', 'SMA_200', 'is_red']].values.flatten()
        rolling_data.append(window)
        indices.append(i)
    return np.array(rolling_data), indices

# Criar janelas deslizantes e prever
X_nov7, indices = create_rolling_window(df_nov7, window_size=60)

# Previsão por vela
print("Backtest para 7 de Novembro de 2024 - Previsões por Vela:")
print("Índice | Data e Hora       | Real | Previsto")

for i, idx in enumerate(indices):
    row = X_nov7[i].reshape(1, -1)  # Reshape para uma única amostra
    predicted_proba = model.predict_proba(row)
    predicted = np.argmax(predicted_proba, axis=1)[0]  # Classe prevista
    actual = df_nov7['Target_3_red'].iloc[idx]
    datetime_val = df_nov7['datetime'].iloc[idx]
    print(f"{idx} | {datetime_val} | {actual} | {predicted}")
