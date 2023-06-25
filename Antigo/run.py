from production.envs.simulation import *
from production.envs.simulation import ProductionEnv
from tensorforce.environments import Environment
from tensorforce.execution import Runner
import log
import logging
import sys

logging.info('<-------------------- INÍCIO DA EXECUÇÃO -------------------->')


timesteps = 100  # Set time steps per episode
#episodes = 10 ** 3  # Set number of episodes

#timesteps = 2  # Set time steps per episode
episodes = 100 # Set number of episodes

logging.info(f'Time Steps: {timesteps}')
logging.info(f'Episodes: {episodes}')

environment_production = Environment.create(environment=ProductionEnv,
                                            max_episode_timesteps=timesteps)

# Tensorforce runner
runner = Runner(agent='rl_config/agent.json', environment=environment_production, )
environment_production.agents = runner.agent



# Run training
runner.run(num_episodes = episodes)

logging.info('<---------------------- FIM DA EXECUÇÃO --------------------->')
