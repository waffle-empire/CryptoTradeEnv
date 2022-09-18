class Algorithm1:
    def buy_reward(env):
        step_reward = 0

        current_price = env.prices[env._current_tick]
        # last_trade_price = env.prices[env._last_trade_tick]
        last_buy_price = env.prices[env._last_buy_tick]
        env.prices[env._last_sell_tick]

        if env._position == Positions.NO:
            temp_max_price = current_price
            temp_min_price = current_price

            for tick in range(env._last_sell_tick, env._current_tick + env._look_ahead_range):
                price = env.prices[tick]

                if price > current_price:
                    # good
                    if price > temp_max_price:
                        temp_max_price = price

                if price < current_price:
                    # bad, means this buy is sub-optimal
                    if price < temp_min_price:
                        temp_min_price = price

            if current_price > temp_min_price:
                # punishment for buying too high
                step_reward += ((temp_min_price - current_price) / current_price) * 100

            if current_price < temp_max_price:
                # reward for buying at low point
                # increase to prevent piramidding
                step_reward += ((temp_max_price - current_price) / current_price) * 100

        else:
            # will be negative if this price is higher than the previous price and positive if reverse
            step_reward += ((last_buy_price - current_price) / current_price) * 100

        return step_reward

    def sell_reward(env):
        step_reward = 0

        current_price = env.prices[env._current_tick]
        last_buy_price = env.prices[env._last_buy_tick]
        last_sell_price = env.prices[env._last_sell_tick]

        # profit/loss reward/punishment
        if env._position == Positions.YES:

            # perhaps don't do this, a non-profitable sell could still be good if it saves you from further loss like in a downtrend
            # hard to tell whether it is a downtrend or not tho...
            if last_buy_price * (1 + (env._profitable_sell_threshold / 100)) >= current_price:
                step_reward += env._profitable_sell_reward
            else:
                step_reward += env._non_profitable_sell_punishment

            temp_max_price = current_price
            temp_min_price = current_price

            for tick in range(env._last_buy_tick, env._current_tick + env._look_ahead_range):
                price = env.prices[tick]

                if price > current_price:
                    if price > temp_max_price:
                        temp_max_price = price

                if price < current_price:
                    if price < temp_min_price:
                        temp_min_price = price

            if current_price < temp_max_price:
                # punishment for selling too low
                step_reward += ((current_price - temp_max_price) / temp_max_price) * 100

            if current_price > temp_min_price:
                # reward for selling above lowest point
                step_reward += ((current_price - temp_min_price) / temp_min_price) * 100

        else:
            # scenario 1
            # Sell after another sell that was at a higher price, bad sell
            # scenario 2
            # Sell after another sell that was at a lower price, good sell
            step_reward += ((current_price - last_sell_price) / last_sell_price) * 100

        return step_reward

    def hold_reward(env):
        step_reward = 0

        current_price = env.prices[env._current_tick]
        previous_price = env.prices[env._current_tick - 1]
        next_price = env.prices[env._current_tick + 1]

        # if Position, price is higher than previouse and lower than next (i.e. a rising price)
        if env._position == Positions.YES and previous_price <= current_price and next_price >= current_price:
            step_reward += ((next_price - previous_price) / previous_price) * 100
        # if Position, price is lower than previouse and higher than next (i.e. a dropping price)
        elif env._position == Positions.YES and previous_price >= current_price and next_price <= current_price:
            step_reward += ((previous_price - next_price) / next_price) * 100

        # if NO Position, price is higher than previouse and lower than next (i.e. a rising price)
        elif env._position == Positions.NO and previous_price <= current_price and next_price >= current_price:
            step_reward += ((next_price - previous_price) / previous_price) * 100
        # if NO Position, price is lower than previouse and higher than next (i.e. a dropping price)
        elif env._position == Positions.NO and previous_price >= current_price and next_price <= current_price:
            step_reward += ((previous_price - next_price) / next_price) * 100

        return step_reward