import pandas as pd
import numpy as np

def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=window).mean()

def calculate_vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, window: int = 100) -> pd.Series:
    typical_price = (high + low + close) / 3
    # Use rolling window for continuous stream VWAP
    return (typical_price * volume).rolling(window=window, min_periods=1).sum() / volume.rolling(window=window, min_periods=1).sum()

def calculate_fibonacci(high: pd.Series, low: pd.Series, window: int = 100) -> pd.DataFrame:
    roll_max = high.rolling(window=window, min_periods=1).max()
    roll_min = low.rolling(window=window, min_periods=1).min()
    diff = roll_max - roll_min
    
    return pd.DataFrame({
        'Fib_236': roll_max - 0.236 * diff,
        'Fib_382': roll_max - 0.382 * diff,
        'Fib_500': roll_max - 0.5 * diff,
        'Fib_618': roll_max - 0.618 * diff
    })

def calculate_sma(data: pd.Series, window: int = 14) -> pd.Series:
    return data.rolling(window=window).mean()

def calculate_ema(data: pd.Series, window: int = 14) -> pd.Series:
    return data.ewm(span=window, adjust=False).mean()

def calculate_rsi(data: pd.Series, window: int = 14) -> pd.Series:
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    exp1 = data.ewm(span=fast, adjust=False).mean()
    exp2 = data.ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line
    return macd, signal_line, histogram

def calculate_bollinger_bands(data: pd.Series, window: int = 20, num_std_dev: int = 2):
    sma = data.rolling(window=window).mean()
    rolling_std = data.rolling(window=window).std()
    upper_band = sma + (rolling_std * num_std_dev)
    lower_band = sma - (rolling_std * num_std_dev)
    return upper_band, lower_band

def compute_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes technical indicators for a given DataFrame of OHLCV data.
    df expects columns: ['close', 'high', 'low', 'open', 'volume']
    """
    df = df.copy()
    
    if 'close' not in df.columns:
        return df

    close = df['close']
    high = df['high']
    low = df['low']
    volume = df['volume']
    
    df['SMA_20'] = calculate_sma(close, 20)
    df['SMA_50'] = calculate_sma(close, 50)
    df['EMA_20'] = calculate_ema(close, 20) # Changed to 20 per requirements
    df['EMA_50'] = calculate_ema(close, 50) # Changed to 50 per requirements
    df['EMA_9'] = calculate_ema(close, 9)
    df['EMA_21'] = calculate_ema(close, 21)
    
    df['RSI_14'] = calculate_rsi(close, 14)
    
    macd, signal, hist = calculate_macd(close)
    df['MACD'] = macd
    df['MACD_Signal'] = signal
    df['MACD_Hist'] = hist
    
    upper, lower = calculate_bollinger_bands(close)
    df['BB_Upper'] = upper
    df['BB_Lower'] = lower
    
    df['ATR_14'] = calculate_atr(high, low, close)
    df['VWAP'] = calculate_vwap(high, low, close, volume)
    
    fibs = calculate_fibonacci(high, low)
    for col in fibs.columns:
        df[col] = fibs[col]
    
    # Fill NAs to avoid NaN issues during ML prediction
    # Bfill then fillna(0) for any remaining at the start
    df.bfill(inplace=True)
    df.fillna(0, inplace=True)
    
    return df
