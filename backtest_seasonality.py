import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

# 조건 체크하는 함수
def check_conditions(timestamp, amt, last_positions):
    dt = pd.to_datetime(timestamp, unit='ms')
    min5 = dt.minute // 5 * 5
    
    new_positions = {
        'first': last_positions['first'],
        'second': last_positions['second'],
        'third': last_positions['third']
    }
    
    # 첫번째 기준
    if min5 in [5, 20, 35, 50]:
        new_positions['first'] = 0.1
    elif min5 in [0, 10, 25, 40]:
        new_positions['first'] = -0.1

    # 두번째 기준
    if dt.hour in [2, 15, 18]:
        new_positions['second'] = 0.1
    elif dt.hour in [12, 16, 21]:
        new_positions['second'] = -0.1

    # 세번째 기준
    if dt.weekday() in [0, 3]:
        new_positions['third'] = 0.1
    elif dt.weekday() in [2, 6]:
        new_positions['third'] = -0.1

    return new_positions


# 백테스트 실행 함수
def backtest(symbol):
    data = pd.read_feather(f'/data/bybit/5m/0/{symbol}.feather')
    data['amount'] = data['close'] * data['volume']
    data['amount_7d'] = data['amount'].rolling(12*24*7).sum()
    data = data[data['dtime'] >= '2023-01-01']
    
    last_positions = {'first': 0, 'second': 0, 'third': 0}
    combined_positions = []
    for ts, amt in zip(data['dtime'], data['amount_7d']):
        last_positions = check_conditions(ts, amt, last_positions)
        combined_position = sum(last_positions.values())
        combined_positions.append(combined_position)
    
    data['position'] = combined_positions
    
    data['next_5min_close'] = data['close'].shift(-1)
    data['5min_return'] = (data['next_5min_close'] - data['close']) / data['close']
    
    data['return'] = data['5min_return'] * data['position']
    # fee 0.075%
    data['fee'] = abs(data['position'].shift(-1) - data['position']) * 0.00075
    data['return'] = data['return'] - data['fee']
    
    data['balance'] = (1 + data['return']).cumprod()
    data = data.dropna()
    
    return data['balance'].tolist()

# 결과 계산 함수
def calculate_metrics(balance):
    # CAGR
    years = len(balance) / (365 * 24 * 12)  # Assuming data for multiple years and 5 min bars
    CAGR = (balance[-1] / balance[0]) ** (1 / years) - 1
    
    # SR (Sharpe Ratio) - Assuming risk free rate as 0
    returns = [balance[i] / balance[i - 1] - 1 for i in range(1, len(balance))]
    try:
        SR = (CAGR - 0) / (pd.Series(returns).std() * (252**0.5))
    except:
        SR = 0
    
    # MDD (Maximum Drawdown)
    rolling_max = pd.Series(balance).expanding().max()
    drawdown = rolling_max - balance
    MDD = drawdown.max()
    
    # complex to real
    CAGR, SR, MDD = np.real(CAGR), np.real(SR), np.real(MDD)
    return CAGR, SR, MDD

# 메인 실행 코드
if __name__ == "__main__":
    symbols = sorted([f for f in os.listdir('/data/bybit/5m/0/') if f.endswith('.feather')])
    
    total_balance = []
    for symbol in symbols:
        symbol_name = symbol.split(".")[0]
        balance = backtest(symbol_name)
        if len(balance) == 0:
            continue
        total_balance.append(balance)
        print(f"Backtest finished for {symbol_name}")
        print(f"Balance: {balance[0]:.2f} -> {balance[-1]:.2f}")
        
        # 결과 계산 및 출력
        CAGR, SR, MDD = calculate_metrics(balance)
        print(f"For {symbol_name}: CAGR = {CAGR:.2%}, SR = {SR:.2f}, MDD = {MDD:.2%}")

    mean_balance = pd.DataFrame(total_balance).mean(axis=0).tolist()
    plt.figure(figsize=(12, 6))
    plt.plot(mean_balance)
    plt.title(f"Mean Balance over time")
    plt.xlabel("Time")
    plt.ylabel("Balance")
    plt.show()
    plt.savefig('mean_balance.png')
    CAGR, SR, MDD = calculate_metrics(mean_balance)
    print(f"Mean CAGR = {CAGR:.2%}, SR = {SR:.2f}, MDD = {MDD:.2%}")
