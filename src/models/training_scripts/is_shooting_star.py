import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_predict, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import pandas_ta as ta
import time
import joblib

# Caminho para os dados
data_path = '../../data/GBPUSD/GBPUSD15.csv'

# Carregar os dados
df = pd.read_csv(data_path)

# Renomear colunas
df.columns = ['date', 'time_only', 'open', 'high', 'low', 'close', 'volume']
df['date'] = pd.to_datetime(df['date'])

# Filtrar os dados para manter apenas as linhas a partir de 2022
df = df[df['date'] >= '2022-01-01']

# Converter a coluna 'time_only' para datetime e extrair a hora como uma feature
df['hour'] = pd.to_datetime(df['time_only'], format='%H:%M:%S').dt.hour

# Filtrar os dados para treinar apenas entre as 10:00 e as 20:00
df = df[(df['hour'] >= 10) & (df['hour'] <= 20)]

# Calcular SMA de 200 períodos
df['SMA_200'] = ta.sma(df['close'], length=200)

# Calcular RSI de 10 períodos
df['RSI_10'] = ta.rsi(df['close'], length=10)

# Função para identificar uma "shooting star" com sombras superior e inferior
def is_shooting_star(candle):
    body = candle['open'] - candle['close']
    upper_shadow = candle['high'] - max(candle['close'], candle['open'])
    lower_shadow = min(candle['close'], candle['open']) - candle['low']
    
    # Critérios para "shooting star" com sombras longas e corpo pequeno
    is_bearish = candle['close'] < candle['open']
    small_body = body < upper_shadow * 0.55        
    long_upper_shadow = upper_shadow > 2 * body                                         

    return is_bearish and small_body and long_upper_shadow

# Identificar "shooting stars" no dataframe
df['is_shooting_star'] = df.apply(is_shooting_star, axis=1)

# Criar janelas deslizantes com base nas últimas 60 velas antes da "shooting star"
def create_rolling_window_features(data, window_size=60):
    rolling_features = []
    rolling_targets = []
    
    for i in range(window_size, len(data) - 1):
        # Checar se a vela atual é uma "shooting star"
        if data['is_shooting_star'].iloc[i]:
            # Verificar se a vela anterior é verde
            previous_candle = data.iloc[i - 1]
            previous_body = previous_candle['close'] - previous_candle['open']
            shooting_star_range = data['high'].iloc[i] - data['low'].iloc[i]
            
            if (previous_candle['close'] > previous_candle['open'] and 
                abs(previous_body) >= 0.7 * shooting_star_range):
                
                # Features das últimas 60 velas antes da "shooting star"
                window = data.iloc[i - window_size:i][['open', 'high', 'low', 'close', 'volume', 'RSI_10', 'SMA_200']].values.flatten()
                rolling_features.append(window)
                
                # Target para a vela após a "shooting star"
                target = data['close'].iloc[i + 1] > data['open'].iloc[i + 1]
                rolling_targets.append(int(target))
    
    return np.array(rolling_features), np.array(rolling_targets)

# Gerar features e targets com base nas janelas deslizantes
X, y = create_rolling_window_features(df, window_size=60)

# Verificar o balanceamento das classes
unique, counts = np.unique(y, return_counts=True)
print(f"Distribuição das classes no conjunto de dados: {dict(zip(unique, counts))}")

# Dividir os dados em treino e teste
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Instanciar o modelo RandomForestClassifier com ajustes para evitar overfitting
model = RandomForestClassifier(n_estimators=10, 
                               max_depth=10, 
                               min_samples_split=10, 
                               random_state=42, 
                               class_weight='balanced')

start_time = time.time()

# Treinar o modelo
model.fit(X_train, y_train)

# Fazer previsões no conjunto de teste
y_pred = model.predict(X_test)

# Calcular o tempo de execução
end_time = time.time()
execution_time = end_time - start_time

# Avaliar a performance do modelo no conjunto de teste
accuracy = accuracy_score(y_test, y_pred)
report = classification_report(y_test, y_pred)

# Validação cruzada estratificada e matriz de confusão
strat_kfold = StratifiedKFold(n_splits=5)
y_pred_cv = cross_val_predict(model, X, y, cv=strat_kfold)
conf_matrix = confusion_matrix(y, y_pred_cv)

# Exibir resultados
print(f"Accuracy: {accuracy}")
print("Classification Report:")
print(report)
print("Confusion Matrix from Cross-Validation:")
print(conf_matrix)
print(f"Tempo de execução: {execution_time:.2f} segundos")

# Salvar o modelo treinado
joblib.dump(model, '../trained_models/random_forest_shooting_star.pkl')
