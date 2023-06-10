from production.envs.simulation import *
from production.envs.simulation import ProductionEnv
from tensorforce.environments import Environment
from tensorforce.execution import Runner


#timesteps = 10 ** 2  # Set time steps per episode
#episodes = 10 ** 2  # Set number of episodes

timesteps = 1  # Set time steps per episode
episodes = 1 # Set number of episodes


environment_production = Environment.create(environment=ProductionEnv,
                                            max_episode_timesteps=timesteps)

# Tensorforce runner
runner = Runner(agent='rl_config/agent.json', environment=environment_production)
environment_production.agents = runner.agent



# Run training
runner.run(num_episodes = episodes)
