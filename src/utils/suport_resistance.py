import MetaTrader5 as mt5
import pandas as pd
import time

# Função para conectar ao MT5
def connect_mt5():
    if not mt5.initialize():
        print("Failed to initialize MT5")
        return False
    else:
        print("Connected to MT5 successfully.")
        return True

# Função para obter dados do ativo
def get_data(symbol, timeframe, n_candles):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n_candles)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

# Função para calcular os níveis de suporte e resistência mais próximos do preço atual
def find_nearest_support_resistance(symbol, window=11520):
    # Obter os dados recentes
    df = get_data(symbol, mt5.TIMEFRAME_M5, window)

    # Obter o preço atual da última vela do DataFrame
    current_price = df['close'].iloc[-1]

    # Encontrar os níveis de suporte e resistência
    high_prices = df['high']
    low_prices = df['low']

    # Resistência: nível mais alto acima do preço atual
    resistance_levels = high_prices[high_prices > current_price]
    closest_resistance = resistance_levels.min() if not resistance_levels.empty else None

    # Suporte: nível mais baixo abaixo do preço atual
    support_levels = low_prices[low_prices < current_price]
    closest_support = support_levels.max() if not support_levels.empty else None

    print(f"Preço atual: {current_price}")
    print(f"Resistência mais próxima: {closest_resistance}")
    print(f"Suporte mais próximo: {closest_support}")

    return closest_resistance, closest_support

# Função principal para executar o script
def main():
    if not connect_mt5():
        return

    symbol = "GBPUSD"  # Substitua pelo símbolo desejado
    resistance, support = find_nearest_support_resistance(symbol)

    # Desconectar do MT5
    mt5.shutdown()

if __name__ == "__main__":
    main()
