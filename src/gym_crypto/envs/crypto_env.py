import numpy as np

from utils import Actions, Positions

class CryptoEnv(gym.Env):
    metadata = {'render.modes': ['human']}

    def __init__(self, df, window_size, frame_bound, reward_algo):
        self.df = df
        self.window_size = window_size
        self.prices, self.signal_features = self._process_data()
        self.shape = (window_size, self.signal_features.shape[1])

        self.frame_bound = frame_bound

        # spaces
        self.action_space = spaces.Discrete(len(Actions))
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=self.shape, dtype=np.float32)

        # episode
        self._start_tick = self.window_size
        self._end_tick = len(self.prices) - 1
        self._done = None
        self._current_tick = None
        self._last_trade_tick = None
        self._last_sell_tick = None
        self._last_buy_tick = None
        self._position = None
        self._position_history = None
        self._action = None
        self._action_history = None
        self._total_reward = None
        self._total_profit = None
        self._first_rendering = None
        self.history = None

        self.trade_fee_bid_percent = 0.075  # percentage
        self.trade_fee_ask_percent = 0.075  # percentage

        self._look_ahead_range = 5

        self._profitable_sell_threshold = 1  # %
        self._profitable_sell_reward = 1
        self._non_profitable_sell_punishment = -self._profitable_sell_reward

        self.reward_algo = reward_algo
        self.reward_history = []

    def _process_data(self):
        prices = self.df.loc[:, 'Close'].to_numpy()

        prices[self.frame_bound[0] - self.window_size]  # validate index (TODO: Improve validation)
        prices = prices[self.frame_bound[0] - self.window_size : self.frame_bound[1]]

        diff = np.insert(np.diff(prices), 0, 0)
        signal_features = np.column_stack((prices, diff))

        return prices, signal_features

    def _calculate_reward(self, action):
        step_reward = 0

        if action == Actions.BUY.value:
            step_reward = self.reward_algo.buy_reward(self)
        elif action == Actions.SELL.value:
            step_reward = self.reward_algo.sell_reward(self)
        elif action == Actions.HOLD.value:
            step_reward = self.reward_algo.hold_reward(self)

        return step_reward
    
    def step(self, action):
        self._action = action
        self._done = False
        self._current_tick += 1

        if self._current_tick == self._end_tick:
            self._done = True

        step_reward = self._calculate_reward(self._action)
        self._total_reward += step_reward

        self._update_profit(self._action)

        trade = False
        if (self._action == Actions.BUY.value and self._position == Positions.NO) or (
            self._action == Actions.SELL.value and self._position == Positions.YES
        ):
            trade = True

        if trade:
            self._position = self._position.opposite()
            self._last_trade_tick = self._current_tick

            if self._action == Actions.BUY.value:
                self._last_buy_tick = self._current_tick
            else:
                self._last_sell_tick = self._current_tick

        self._position_history.append(self._position)
        self._action_history.append(self._action)

        observation = self._get_observation()
        info = dict(step_reward=step_reward, total_reward=self._total_reward, total_profit=self._total_profit, position=self._position.value)
        self._update_history(info)

        return observation, step_reward, self._done, info

    def _update_profit(self, action):
        if (action == Actions.SELL.value and self._position == Positions.YES) or self._done:
            current_price = self.prices[self._current_tick]
            last_buy_price = self.prices[self._last_buy_tick]

            if self._position == Positions.YES and self._done:
                shares = (self._total_profit * (1 - self.trade_fee_ask_percent)) / last_buy_price
                self._total_profit = (shares * (1 - self.trade_fee_bid_percent)) * current_price

    def max_possible_profit(self):
        current_tick = self._start_tick
        last_trade_tick = current_tick - 1
        profit = 1.0

        while current_tick <= self._end_tick:
            position = None
            if self.prices[current_tick] < self.prices[current_tick - 1]:
                while current_tick <= self._end_tick and self.prices[current_tick] < self.prices[current_tick - 1]:
                    current_tick += 1
                position = Positions.NO
            else:
                while current_tick <= self._end_tick and self.prices[current_tick] >= self.prices[current_tick - 1]:
                    current_tick += 1
                position = Positions.YES

            if position == Positions.YES:
                current_price = self.prices[current_tick - 1]
                last_trade_price = self.prices[last_trade_tick]
                shares = profit / last_trade_price
                profit = shares * current_price
            last_trade_tick = current_tick - 1

        return profit
    
    def reset(self):
        self._done = False
        self._current_tick = self._start_tick
        self._last_trade_tick = self._current_tick - 1
        self._last_sell_tick = self._current_tick - 1
        self._last_buy_tick = self._current_tick - 1
        self._position = Positions.NO
        self._position_history = (self.window_size * [None]) + [self._position]
        self._action = Actions.HOLD
        self._action_history = (self.window_size * [None]) + [self._action]
        self._total_reward = 0.0
        self._total_profit = 1.0  # unit
        self._first_rendering = True
        self.history = {}
        return self._get_observation()
    
    def _get_observation(self):
        return self.signal_features[(self._current_tick - self.window_size) : self._current_tick]

    def _update_history(self, info):
        if not self.history:
            self.history = {key: [] for key in info.keys()}

        for key, value in info.items():
            self.history[key].append(value)

    def render(self, mode='human'):
        def _plot_position(action, tick):
            color = None
            if action == Actions.BUY:
                color = 'green'
            elif action == Actions.HOLD:
                color = 'blue'
            elif action == Actions.SELL:
                color = 'red'
            if color:
                plt.scatter(tick, self.prices[tick], color=color)

        if self._first_rendering:
            self._first_rendering = False
            plt.cla()
            plt.plot(self.prices)
            start_action = self._action_history[self._start_tick]
            _plot_position(start_action, self._start_tick)

        _plot_position(self._action, self._current_tick)

        plt.suptitle("Total Reward: %.6f" % self._total_reward + ' ~ ' + "Total Profit: %.6f" % self._total_profit)

        plt.pause(0.01)

    def render_all(self):
        window_ticks = np.arange(len(self._action_history))
        plt.plot(self.prices)

        hold_ticks = []
        sell_ticks = []
        buy_ticks = []
        for i, tick in enumerate(window_ticks):
            if self._action_history[i] == Actions.BUY:
                buy_ticks.append(tick)
            elif self._action_history[i] == Actions.HOLD:
                hold_ticks.append(tick)
            elif self._action_history[i] == Actions.SELL:
                sell_ticks.append(tick)

        plt.plot(buy_ticks, self.prices[buy_ticks], 'ro')
        plt.plot(hold_ticks, self.prices[hold_ticks], 'bo')
        plt.plot(sell_ticks, self.prices[sell_ticks], 'go')

        plt.suptitle("Total Reward: %.6f" % self._total_reward + ' ~ ' + "Total Profit: %.6f" % self._total_profit)

    def close(self):
        plt.close()

    def save_rendering(self, filepath):
        plt.savefig(filepath)

    def pause_rendering(self):
        plt.show()