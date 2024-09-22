import MetaTrader5 as mt5

def place_order(symbol, order_type):
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"{symbol} not found, cannot place order")
        return
    
    if not symbol_info.visible:
        print(f"{symbol} is not visible, trying to switch on")
        if not mt5.symbol_select(symbol, True):
            print(f"symbol_select({symbol}) failed, exit")
            return
    
    symbol_info = mt5.symbol_info(symbol) 
    if symbol_info is None:
        print(f"{symbol} is still not found after trying to select it")
        return

    if not symbol_info.visible:
        print(f"{symbol} is still not visible after trying to select it")
        return
    
    point = symbol_info.point
    price = mt5.symbol_info_tick(symbol).ask if order_type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(symbol).bid
    deviation = 20
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": 0.01,
        "type": order_type,
        "price": price,
        #"sl": price - 10000 * point if order_type == mt5.ORDER_TYPE_BUY else price + 100 * point,
        #"tp": price + 10000 * point if order_type == mt5.ORDER_TYPE_BUY else price - 100 * point,
        "deviation": deviation,
        "magic": 234000,
        "comment": "Python script order",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    print(f"Order send result: {result}")
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Order failed: {result.comment}")