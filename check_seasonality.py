import pandas as pd
import os
import glob

def load_data(symbol: str, path='/data/bybit/5m/0') -> pd.DataFrame:
    """Load data from feather file."""
    file_path = os.path.join(path, f"{symbol}USDT:USDT.feather")
    df = pd.read_feather(file_path)
    df['dtime'] = pd.to_datetime(df['dtime'], unit='ms')
    df = df[df['dtime'].between('2022-01-01', '2023-08-01')]
    return df

def calculate_minute_return(df: pd.DataFrame) -> pd.Series:
    """Calculate average 5-minute return normalized by Z-score."""
    df['5m'] = df['dtime'].dt.minute // 5 * 5
    df['next_min_close'] = df['close'].shift(-1)
    df['min_return'] = (df['next_min_close'] - df['close']) / df['close']
    average_min_return = df.groupby('5m')['min_return'].mean()
    return (average_min_return - average_min_return.mean()) / average_min_return.std()

def calculate_hourly_return(df: pd.DataFrame) -> pd.Series:
    """Calculate average hourly return normalized by Z-score."""
    df['hour'] = df['dtime'].dt.hour
    df['next_hourly_close'] = df['close'].shift(-12)
    df['hourly_return'] = (df['next_hourly_close'] - df['close']) / df['close']
    average_hourly_return = df.groupby('hour')['hourly_return'].mean()
    return (average_hourly_return - average_hourly_return.mean()) / average_hourly_return.std()

def calculate_daily_return(df: pd.DataFrame) -> pd.Series:
    """Calculate average daily return normalized by Z-score."""
    df['day'] = df['dtime'].dt.weekday
    df['next_daily_close'] = df['close'].shift(-12*24)
    df['daily_return'] = (df['next_daily_close'] - df['close']) / df['close']
    average_daily_return = df.groupby('day')['daily_return'].mean()
    return (average_daily_return - average_daily_return.mean()) / average_daily_return.std()

if __name__ == '__main__':
    symbols = [os.path.basename(symbol).split('USDT')[0] for symbol in glob.glob('/data/bybit/5m/0/*.feather')]
    
    for symbol in symbols:
        df = load_data(symbol)

        # Calculate returns for different time frames
        minute_returns = calculate_minute_return(df)
        hourly_returns = calculate_hourly_return(df)
        daily_returns = calculate_daily_return(df)

        # Print results for each symbol
        print(f"Symbol: {symbol}")
        print("\n5-Minute Returns:")
        print(minute_returns)
        print("\nHourly Returns:")
        print(hourly_returns)
        print("\nDaily Returns:")
        print(daily_returns)
        print("="*50)
