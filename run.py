from production.envs.simulation import *
from production.envs.simulation import ProductionEnv
from tensorforce.environments import Environment
from tensorforce.execution import Runner


#timesteps = 10 ** 3  # Set time steps per episode
#episodes = 10 ** 3  # Set number of episodes

timesteps = 2  # Set time steps per episode
episodes = 2 # Set number of episodes


environment_production = Environment.create(environment=ProductionEnv,
                                            max_episode_timesteps=timesteps)

# Tensorforce runner
runner = Runner(agent='rl_config/agent.json', environment=environment_production)
environment_production.agents = runner.agent



# Run training
runner.run(num_episodes = episodes)
