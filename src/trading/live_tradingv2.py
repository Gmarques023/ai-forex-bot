import pandas as pd
import MetaTrader5 as mt5
import joblib
import numpy as np
import pandas_ta as ta
from utils.get_last_candle_data_from_csv import get_last_candle_data_from_csv
from trading.place_order import place_order

# Carregar o modelo treinado
model_path = './models/trained_models/random_forestv4.pkl'
model = joblib.load(model_path)

# Função para criar janelas deslizantes com base nas últimas velas selecionadas
def create_rolling_window_features(data, window_size=60):
    if len(data) >= window_size:
        window = data.iloc[-window_size:].copy()  # Copiar a janela de dados

        # Calcular o RSI e a SMA para a janela de dados
        window['RSI_10'] = ta.rsi(window['close'], length=10)
        window['SMA_200'] = ta.sma(window['close'], length=200)

        # Preencher valores NaN gerados pelo RSI e SMA com o último valor válido
        window['RSI_10'] = window['RSI_10'].ffill()
        window['SMA_200'] = window['SMA_200'].ffill()

        # Garantir que não haja NaNs restantes (caso a janela seja pequena para SMA)
        window = window.bfill()

        # Selecionar as features desejadas e achatar os dados
        features = window[['open', 'high', 'low', 'close', 'volume', 'RSI_10', 'SMA_200']].values.flatten()
        return np.array([features])  # Retorna um array com o formato esperado pelo modelo
    
    return np.array([])  # Retorna um array vazio se o tamanho da janela não for suficiente

def live_trading(symbol, csv_file, last_trade_time):
    # Carregar os dados do CSV
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

        # Verificar se esta é uma nova vela
        if candle_time > last_trade_time:
            # Criar features com base nas últimas 60 velas
            rolling_features = create_rolling_window_features(df, window_size=60)
            
            if rolling_features.size > 0:
                print(f"Features para previsão: {rolling_features}")
                
                # Fazer a previsão das probabilidades para a vela atual
                prediction_proba = model.predict_proba(rolling_features)[0]
                print(f"Probabilidade de Sell: {prediction_proba[0]:.2f}, Probabilidade de Buy: {prediction_proba[1]:.2f}")

                # Verificar a previsão da vela anterior
                previous_features = create_rolling_window_features(df.iloc[:-1], window_size=60)  # Excluir a última vela para prever a anterior
                if previous_features.size > 0:
                    previous_prediction_proba = model.predict_proba(previous_features)[0]
                    print(f"Probabilidade de Buy na vela anterior: {previous_prediction_proba[1]:.2f}")
                    print(f"Probabilidade de Sell na vela anterior: {previous_prediction_proba[0]:.2f}")
                    
                    # Condição para Buy
                    #if prediction_proba[1] > 0.5 and previous_prediction_proba[1] > 0.5:
                        # Verificar se o fechamento da vela anterior é maior que a abertura
                    #    previous_candle = df.iloc[-1]  # Penúltima vela
                    #    if previous_candle['close'] > previous_candle['open']:
                    #        print("Probabilidade de Buy > 0.5 e condição da vela anterior satisfeita, colocando ordem de compra.")
                    #        place_order(symbol, mt5.ORDER_TYPE_BUY)
                    #    else:
                    #        print("Condição da vela anterior não satisfeita: fechamento <= abertura, nenhuma ordem de compra colocada.")
                    
                    # Condição para Sell
                    if prediction_proba[0] > 0.5 and previous_prediction_proba[0] > 0.5: 
                        previous_candle = df.iloc[-1] 
                        if previous_candle['close'] < previous_candle['open']:
                            print("Probabilidade de Sell > 0.5 e condição da vela anterior satisfeita, colocando ordem de venda.")
                            place_order(symbol, mt5.ORDER_TYPE_SELL)
                        else:
                            print("Condição da vela anterior não satisfeita: fechamento >= abertura, nenhuma ordem de venda colocada.")
                else:
                    print("Não foi possível calcular a previsão para a vela anterior.")

            return candle_time
        else:
            print("Já foi feita uma negociação para esta vela.")
    return last_trade_time
