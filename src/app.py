import MetaTrader5 as mt5
import os
from dotenv import load_dotenv

load_dotenv()

mt5.initialize(
   "C:\Program Files\FPMarkets MT5 Terminal",   # path to the MetaTrader 5 terminal EXE file
   login=os.getenv('ACCOUNT_NUMBER'),           # account number
   password=os.getenv('ACCOUNT_PASSWORD'),      # password
   server=os.getenv('ACCOUNT_SERVER'),          # server name as it is specified in the terminal                        
)

    # Verifique se a conexão foi bem sucedida
if not mt5.initialize():
    print("Falha ao inicializar o MetaTrader 5.")
else:
    # Símbolo do instrumento 
    symbol = "GBPUSD"
    # Volume da operação (tamanho da posição em lotes)
    volume = 0.10
    # Obtenha o preço de compra atual (ask) do símbolo
    price = mt5.symbol_info_tick(symbol).ask
    # stop loss (SL) e take profit (TP)
    sl = price + 0.00010 
    tp = price - 0.00010  
    # Estrutura do pedido
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": mt5.ORDER_TYPE_SELL,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 20,
        "magic": 234000,
        "comment": "Ordem de compra via Python",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    # Envie o pedido de compra
    result = mt5.order_send(request)
    # Verifique se o pedido foi executado com sucesso
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        print(f"Ordem de compra de {volume} lotes de {symbol} enviada com sucesso.")
        print(f"Preço: {price}, SL: {sl}, TP: {tp}")
        print(f"Número do Pedido: {result.order}")
    else:
        print(f"Falha ao enviar a ordem de compra. Código do erro: {result.retcode}")
