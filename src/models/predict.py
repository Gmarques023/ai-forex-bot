#Script para fazer predições com o modelo treinado

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
import time

data_path = '../data/GBPUSD/GBPUSD15.csv'

df = pd.read_csv(data_path)

df.columns = ['date', 'time', 'open', 'high', 'low', 'close', 'volume']
df['date'] = pd.to_datetime(df['date'], format='%Y.%m.%d')

# Filtrar os dados para manter apenas as linhas a partir de 2022
df = df[df['date'] >= '2022-01-01']
df['Target'] = (df['close'] > df['open']).astype(int)

# Selecionar features e target
features = df[['open', 'high', 'low', 'close']]
target = df['Target']

# Dividir os dados em treino e teste
X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)

# Instanciar o modelo RandomForestClassifier
model = RandomForestClassifier(n_estimators=10, random_state=42)

start_time = time.time()

# Treinar o modelo
model.fit(X_train, y_train)

# Fazer previsões no conjunto de teste
y_pred = model.predict(X_test)

# Calcular o tempo de execução
end_time = time.time()
execution_time = end_time - start_time

# Avaliar a performance do modelo
accuracy = accuracy_score(y_test, y_pred)
report = classification_report(y_test, y_pred)

print(f"Accuracy: {accuracy}")
print("Classification Report:")
print(report)
print(f"Tempo de execução: {execution_time} segundos")