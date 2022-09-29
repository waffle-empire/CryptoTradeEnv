from gym.envs.registration import register

register(
    id='crypto-v0',
    entry_point='gym_crypto.envs:CryptoEnv',
)
