def get_features_from_candle(candle):
    features = candle[['open', 'high', 'low', 'close']].values.reshape(1, -1)
    return features