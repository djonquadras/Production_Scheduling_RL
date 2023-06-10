from logger import *
from production import *
from production.environment import ProductionSystem
from tensorforce.environments import Environment
from tensorforce.execution import Runner

# tf.set_random_seed(10)

timesteps = 10 ** 2  # Set time steps per episode
episodes = 10 ** 2  # Set number of episodes

simulation = Environment.create(environment='production.envs.ProductionSystem',
                                max_episode_timesteps=timesteps)

# Tensorforce runner
runner = Runner(agent='rl_config/agent.json',
                environment = simulation)

simulation.agents = runner.agent

# Run training
runner.run(num_episodes=episodes)

simulation.environment.statistics.update({'time_end': simulation.environment.env.now})

export_statistics_logging(statistics = simulation.environment.statistics,
                          parameters = simulation.environment.parameters,
                          resources = simulation.environment.resources)


'''
from tensorforce.environments import Environment
from tensorforce.agents import Agent
import numpy as np

class CustomEnvironment(Environment):

    def __init__(self):
        super().__init__()

    def states(self):
        return dict(type='float', shape=(8,))

    def actions(self):
        return dict(type='int', num_values=4)

    # Optional: should only be defined if environment has a natural fixed
    # maximum episode length; otherwise specify maximum number of training
    # timesteps via Environment.create(..., max_episode_timesteps=???)
    def max_episode_timesteps(self):
        return super().max_episode_timesteps()

    # Optional additional steps to close environment
    def close(self):
        super().close()

    def reset(self):
        state = np.random.random(size=(8,))
        return state

    def execute(self, actions):
        next_state = np.random.random(size=(8,))
        terminal = False  # Always False if no "natural" terminal state
        reward = np.random.random()
        return next_state, terminal, reward
    

environment = Environment.create(
    environment=CustomEnvironment, max_episode_timesteps=100
)


agent = Agent.create(
    agent='ppo', environment=environment, batch_size=10, learning_rate=1e-3
)

for _ in range(100):
    states = environment.reset()
    terminal = False
    while not terminal:
        actions = agent.act(states=states)
        states, terminal, reward = environment.execute(actions=actions)
        agent.observe(terminal=terminal, reward=reward)
'''

