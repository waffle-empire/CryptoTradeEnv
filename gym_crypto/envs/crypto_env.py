import numpy as np

from .trading_env import *


class CryptoEnv(TradingEnv):
    def __init__(self, df, window_size, frame_bound):
        # assert len(frame_bound) == 2

        self.frame_bound = frame_bound
        super().__init__(df, window_size)

        self.trade_fee_bid_percent = 0.01  # percentage of value
        self.trade_fee_ask_percent = 0.01  # percentage of value

        self._tick_range = 10
        self._reward_bonus = 1

        self._look_ahead_range = 5

        self._profitable_sell_threshold = 1 # %
        self._profitable_sell_reward = 1
        self._non_profitable_sell_punishment = -1

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
            step_reward = self.buy_reward()
        elif action == Actions.SELL.value:
            step_reward = self.sell_reward()
        elif action == Actions.HOLD.value:
            step_reward = self.hold_reward()

        # current_price = self.prices[self._current_tick]
        # # last_trade_price = self.prices[self._last_trade_tick]
        # last_buy_price = self.prices[self._last_buy_tick]
        # last_sell_price = self.prices[self._last_sell_tick]

        # if action == Actions.BUY.value and self._position == Positions.NO:
        #     # BUY
        #     # check previous values if trend is downward up to buy point
        #     p_lowest = current_price
        #     imperfect = False
            
        #     for tick in range(self._current_tick-self._tick_range, self._current_tick):
        #         curr_price = self.prices[tick]

        #         if curr_price < current_price:
        #             #bad
        #             imperfect = True
        #             if curr_price < p_lowest:
        #                 p_lowest = curr_price

        #         elif curr_price > current_price:
        #             #good
        #             step_reward += self._reward_bonus
                
        #     if imperfect:
        #         step_reward -= ((current_price - p_lowest) / p_lowest) * 100

        #     p_lowest = current_price
        #     imperfect = False

        #     # check next values if trend is upward
        #     for tick in range(self._current_tick, self._current_tick+self._tick_range):
        #         curr_price = self.prices[tick]

        #         if curr_price < current_price:
        #             #bad
        #             imperfect = True
        #             if curr_price < p_lowest:
        #                 p_lowest = curr_price

        #         elif curr_price > current_price:
        #             #good
        #             step_reward += self._reward_bonus

        #     if imperfect:
        #         step_reward -= ((current_price - p_lowest) / p_lowest) * 100

        # elif action == Actions.SELL.value and self._position == Positions.YES:
        #     # SELL
        #     # check previous values if trend is upward
        #     p_highest = current_price
        #     test_before = False
        #     test_after = False
            
        #     for tick in range(self._last_buy_tick, self._current_tick):
        #         curr_price = self.prices[tick]

        #         if curr_price < current_price:
        #             #good
        #             step_reward += self._reward_bonus

        #         elif curr_price > current_price:
        #             #bad
        #             test_before = True
        #             if curr_price > p_highest:
        #                 p_highest = curr_price
                
        #     # if imperfect:
        #     #     step_reward -= ((p_highest - current_price) / current_price) * 100

        #     p_highest = current_price

        #     # check next values if trend is downward
        #     for tick in range(self._current_tick, self._current_tick+self._tick_range):
        #         curr_price = self.prices[tick]

        #         if curr_price < current_price:
        #             #good
        #             step_reward += self._reward_bonus

        #         elif curr_price > current_price:
        #             #bad
        #             test_after = True
        #             if curr_price > p_highest:
        #                 p_highest = curr_price

        #     if test_before and test_after:
        #         step_reward -= ((p_highest - current_price) / current_price) * 100
            
        #     step_reward += (last_buy_price / current_price) / current_price
       
        # elif action == Actions.HOLD.value:
        #     # HOLD
        #     # check if value is higher than last buy
        #     if self._position == Positions.YES:
        #         if current_price >= last_buy_price:
        #             step_reward += self._reward_bonus
        #         else:
        #             step_reward -= self._reward_bonus
            
        #     # check next values if trend is upward for at least 1 candle
        #     if self.prices[self._current_tick+1] >= current_price:
        #         step_reward += self._reward_bonus
        #     else:
        #         step_reward -= self._reward_bonus

        # elif action == Actions.BUY.value and self._position == Positions.YES:
        #     # BUY when position was True or SELL when position was False
        #     if current_price < last_buy_price:
        #         reward += self._reward_bonus/10
        #     else:
        #         reward -= self._reward_bonus
        
        # elif action == Actions.SELL.value and self._position == Positions.NO:
            # BUY when position was True or SELL when position was False
            if current_price > last_sell_price:
                reward += self._reward_bonus/10
            else:
                reward -= self._reward_bonus


            pass

        return step_reward
    
    def buy_reward(self):
        pass

    def sell_reward(self):
        step_reward = 0

        current_price = self.prices[self._current_tick]
        # last_trade_price = self.prices[self._last_trade_tick]
        last_buy_price = self.prices[self._last_buy_tick]
        last_sell_price = self.prices[self._last_sell_tick]

        # profit/loss reward/punishment
        if self._position == Positions.YES:

            # perhaps don't do this, a non-profitable sell could still be good if it saves you from further loss like in a downtrend
            # hard to tell whether it is a downtrend or not tho...
            if last_buy_price * ( 1 + ( self._profitable_sell_threshold / 100 ) ) >= current_price:
                step_reward += self._profitable_sell_reward
            else:
                step_reward += self._non_profitable_sell_punishment
        
            temp_max_price = current_price
            temp_min_price = current_price

            for tick in range(self._last_buy_tick, self._current_tick + self._look_ahead_range):
                price = self.prices[tick]

                if price > current_price:
                    if price > temp_max_price:
                        temp_max_price = price

                if price < current_price:
                    if price < temp_min_price:
                        temp_min_price = price

            if current_price < temp_max_price:
                #punishment for selling too low
                step_reward += ( (current_price - temp_max_price) / temp_max_price ) * 100

            else:
                #reward for selling at highest point
                step_reward += ( (current_price - temp_min_price) / temp_min_price ) * 100
            
        else:
            #scenario 1
            #Sell after another sell that was at a higher price, bad sell
            if current_price > last_sell_price:
                step_reward += ( (current_price - last_sell_price) / last_sell_price ) * 100
            
            #scenario 2
            #Sell after another sell that was at a lower price, good sell 
            if current_price > last_sell_price:
                step_reward += ( (current_price - last_sell_price) / last_sell_price ) * 100

        return step_reward
        

    def hold_reward(self):
        pass

    def _update_profit(self, action):
        trade = False
        if (action == Actions.BUY.value and self._position == Positions.NO) or (
            action == Actions.SELL.value and self._position == Positions.YES
        ):
            trade = True

        if trade or self._done:
            current_price = self.prices[self._current_tick]
            last_trade_price = self.prices[self._last_trade_tick]

            if self._position == Positions.YES:
                shares = (self._total_profit * (1 - self.trade_fee_ask_percent)) / last_trade_price
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
