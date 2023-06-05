# Methods - Environment

def step_to_export(agent):
        return ((agent.counter % agent.parameters["EXPORT_FREQUENCY"] == 0 or
                 agent.counter % agent.max_episode_timesteps() == 0) and not
                 agent.parameters["EXPORT_NO_LOGS"])

def last_episode(agent):
    return(agent.counter == agent.max_episode_timesteps())