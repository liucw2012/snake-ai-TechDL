import math

import gym
import numpy as np

from snake_game import SnakeGame

class SnakeEnv(gym.Env):
    def __init__(self, seed=0, board_size=21, silent_mode=True):
        super().__init__()
        self.game = SnakeGame(seed=seed, board_size=board_size, silent_mode=silent_mode)
        self.game.reset()

        self.action_space = gym.spaces.Discrete(4) # 0: UP, 1: LEFT, 2: RIGHT, 3: DOWN
        
        self.observation_space = gym.spaces.Box(
            low=0, high=255,
            shape=(84, 84, 3),
            dtype=np.uint8
        )

        self.base_food_reward = 4.5
        self.reward_boost_factor = 4.0

        self.board_size = board_size
        self.grid_size = board_size ** 2 # Max length of snake is board_size^2
        self.init_snake_size = len(self.game.snake)
        self.max_growth = self.grid_size - self.init_snake_size
        self.median_size = self.init_snake_size + self.max_growth / 2

        self.done = False
        self.reward_step_counter = 0

    def reset(self):
        self.game.reset()

        self.done = False
        self.reward_step_counter = 0

        obs = self._generate_observation()
        return obs
    
    def step(self, action):
        self.done, info = self.game.step(action) # info = {"snake_size": int, "snake_head_pos": np.array, "prev_snake_head_pos": np.array, "food_pos": np.array, "food_obtained": bool}
        obs = self._generate_observation()

        reward = 0.0
        self.reward_step_counter += 1

        if info["food_obtained"]: # food eaten
            # Reward on num_steps between getting food.
            reward_speed = math.pow(self.base_food_reward, (self.grid_size - self.reward_step_counter) / self.grid_size)
            reward_speed = reward_speed / self.base_food_reward * self.reward_boost_factor # Normalize to (0, 1) * self.reward_boost_factor.

            info["food_reward_on_speed"] = reward_speed
            
            reward = reward_speed

            # info["reward_step_counter"] = self.reward_step_counter # Save reward step counter for debugging
            self.reward_step_counter = 0 # Reset reward step counter
        
        elif self.done: # Snake bumps into wall or itself. Episode is over.
            # Game Over penalty is based on snake size.
            reward = - math.pow(self.max_growth, (self.grid_size - info["snake_size"]) / self.grid_size)
        
        else:
            # Give a tiny reward/penalty to the agent based on whether it is heading towards the food or not.
            # Not competing with game over penalty or the food eaten reward.
            if np.linalg.norm(info["snake_head_pos"] - info["food_pos"]) < np.linalg.norm(info["prev_snake_head_pos"] - info["food_pos"]):
                reward = 1 / info["snake_size"]
            else:
                reward = - 1 / info["snake_size"]
            info["step_reward"] = reward


        # max_score: 438 * 4 (food reward) - 1 = 1751
        # low_score: -438 (direct lose) 
        reward = reward * 0.01 # Scale reward to be in range [-4.38, 17.51]

        return obs, reward, self.done, info
    
    def render(self):
        self.game.render()

    def get_action_mask(self):
        return np.array([[self._check_action_validity(a) for a in range(self.action_space.n)]])
    
    # Check if the action is against the current direction of the snake or is ending the game.
    def _check_action_validity(self, action):
        current_direction = self.game.direction
        snake_list = self.game.snake
        row, col = snake_list[0]
        if action == 0: # UP
            if current_direction == "DOWN":
                return False
            else:
                row -= 1

        elif action == 1: # LEFT
            if current_direction == "RIGHT":
                return False
            else:
                col -= 1

        elif action == 2: # RIGHT 
            if current_direction == "LEFT":
                return False
            else:
                col += 1     
        
        elif action == 3: # DOWN 
            if current_direction == "UP":
                return False
            else:
                row += 1

        # Check if snake collided with itself or the wall
        game_over = (
            (row, col) in snake_list
            or row < 0
            or row >= self.board_size
            or col < 0
            or col >= self.board_size
        )

        if game_over:
            return False
        else:
            return True

    # EMPTY: BLACK; SnakeBODY: GRAY; SnakeHEAD: GREEN; FOOD: RED;
    def _generate_observation(self):
        obs = np.zeros((self.game.board_size, self.game.board_size), dtype=np.uint8)
        obs[tuple(np.transpose(self.game.snake))] = 200
        # Stack single layer into 3-channel-image.
        obs = np.stack((obs, obs, obs), axis=-1)
        
        # Set the snake head to green
        obs[tuple(self.game.snake[0])] = [0, 255, 0]

        # Set the food to red
        obs[tuple(self.game.food)] = [0, 0, 255]

        # Enlarge the observation to 84x84
        obs = np.repeat(np.repeat(obs, 4, axis=0), 4, axis=1)

        return obs

# Test the environment using random actions
NUM_EPISODES = 100
RENDER_DELAY = 0.001
from matplotlib import pyplot as plt

if __name__ == "__main__":
    env = SnakeEnv(silent_mode=False)
    
    # # Test Init Efficiency
    # print(MODEL_PATH_S)
    # print(MODEL_PATH_L)
    # num_success = 0
    # for i in range(NUM_EPISODES):
    #     num_success += env.reset()
    # print(f"Success rate: {num_success/NUM_EPISODES}")

    # sum_reward = 0

    # # 0: UP, 1: LEFT, 2: RIGHT, 3: DOWN
    # action_list = [1, 1, 1, 0, 0, 0, 2, 2, 2, 3, 3, 3]
    
    # for _ in range(NUM_EPISODES):
    #     obs = env.reset()
    #     done = False
    #     i = 0
    #     while not done:
    #         plt.imshow(obs, interpolation='nearest')
    #         plt.show()
    #         action = env.action_space.sample()
    #         # action = action_list[i]
    #         i = (i + 1) % len(action_list)
    #         obs, reward, done, info = env.step(action)
    #         sum_reward += reward
    #         if np.absolute(reward) > 0.001:
    #             print(reward)
    #         env.render()
            
    #         time.sleep(RENDER_DELAY)
    #     # print(info["snake_length"])
    #     # print(info["food_pos"])
    #     # print(obs)
    #     print("sum_reward: %f" % sum_reward)
    #     print("episode done")
    #     # time.sleep(100)
    
    # env.close()
    # print("Average episode reward for random strategy: {}".format(sum_reward/NUM_EPISODES))