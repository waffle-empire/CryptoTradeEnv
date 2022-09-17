# CryptoTradeEnv

attempt at an OpenAI Gym environment for crypto trading, based on [gym-anytrading](https://github.com/AminHP/gym-anytrading)
dataloader is very specific for my usecase and might not be useful for you so use own datasets.

TA-lib required, usually works best with an unofficial whl but whatever install works is fine.
[talib](https://github.com/mrjbq7/ta-lib)

## TODO

create python bindings in C++ Preprocessor for speed enhancement [python-bindings](https://realpython.com/python-bindings-overview/)
use Close_raw for actual profit and reward predictions

## Stable Baselines that allow recurrent networks

- A2C
- ACER
- ACKTR
- PPO2
