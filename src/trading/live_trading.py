import pandas as pd
import MetaTrader5 as mt5
import joblib
import numpy as np
import pandas_ta as ta
from utils.get_last_candle_data_from_csv import get_last_candle_data_from_csv
from trading.place_order import place_order

# Carregar o modelo treinado
model_path = './models/trained_models/random_time_series.pkl'
model = joblib.load(model_path)

# Função para criar janelas deslizantes com base nas últimas velas selecionadas
def create_rolling_window_features(data, window_size=60):
    if len(data) >= window_size:
        window = data.iloc[-window_size:].copy()

        # Calcular o RSI e a SMA
        window['RSI_10'] = ta.rsi(window['close'], length=10)
        window['SMA_200'] = ta.sma(window['close'], length=200)
        
        # Identificar se a vela é vermelha
        window['is_red'] = window['close'] < window['open']
        
        # Preencher valores NaN gerados pelo RSI e SMA com o último valor válido
        window['RSI_10'] = window['RSI_10'].ffill()
        window['SMA_200'] = window['SMA_200'].ffill()
        
        # Garantir que não haja NaNs restantes (caso a janela seja pequena para SMA)
        window = window.bfill()
        
        # Selecionar as features desejadas e achatar os dados
        features = window[['open', 'high', 'low', 'close', 'volume', 'RSI_10', 'SMA_200', 'is_red']].values.flatten()
        return np.array([features])
    
    return np.array([])

def live_trading(symbol, csv_file, last_trade_time):
    df = pd.read_csv(csv_file)
    
    # Renomear colunas
    df.columns = ['date', 'time_only', 'open', 'high', 'low', 'close', 'volume']
    df['date'] = pd.to_datetime(df['date'])
    df['hour'] = pd.to_datetime(df['time_only'], format='%H:%M:%S').dt.hour
    
    # Obter a última vela
    last_candle = get_last_candle_data_from_csv(csv_file)

    if last_candle is not None:
        candle_time = pd.to_datetime(f"{last_candle['date']} {last_candle['time_only']}")
        candle_time = candle_time.replace(tzinfo=None)
        last_trade_time = last_trade_time.replace(tzinfo=None)

        # Executar a previsão para a nova vela
        if candle_time > last_trade_time:
            rolling_features = create_rolling_window_features(df, window_size=60)
            
            if rolling_features.size > 0:
                # Print das features da vela atual
                print(f"Features da vela atual (últimas 60 velas):")
                print(rolling_features)

                prediction_proba = model.predict_proba(rolling_features)[0]
                print(f"Probabilidade de 3 velas vermelhas: {prediction_proba[1]:.2f}")

                previous_features = create_rolling_window_features(df.iloc[:-1], window_size=60)
                if previous_features.size > 0:
                    # Print das features da vela anterior
                    print(f"Features da vela anterior (últimas 60 velas):")
                    print(previous_features)

                    previous_prediction_proba = model.predict_proba(previous_features)[0]
                    print(f"Probabilidade de 3 velas vermelhas consecutivas na vela anterior: {previous_prediction_proba[1]:.2f}")
                    
                    # Condição para Sell (3 velas vermelhas consecutivas previstas)
                    if prediction_proba[1] > 0.01: #and previous_prediction_proba[1] < 0.5:
                        previous_candle = df.iloc[-1]
                        print("Alta probabilidade de 3 velas vermelhas consecutivas, colocando ordem de venda.")
                        place_order(symbol, mt5.ORDER_TYPE_SELL)
                        
                        # Atualizar o last_trade_time somente após realizar a negociação
                        last_trade_time = candle_time
                else:
                    print("Não foi possível calcular a previsão para a vela anterior.")

            return last_trade_time
        else:
            print("Já foi feita uma negociação para esta vela.")
    return last_trade_time
