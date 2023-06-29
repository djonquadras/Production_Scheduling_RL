import random
from collections import deque

from production.envs.machine import *
from production.envs.simulation import *
import numpy as np
import pandas as pd
from datetime import datetime
from collections import Counter
from collections import defaultdict 

PRINT_CONSOLE = False  # Extended print out during running, particularly for debugging
EPSILON = 0.000001  # Small number larger than zero used as "marginal" time step or to compare values
EXPORT_FREQUENCY = 10 ** 3  # Number of steps between csv-export of log-files
EXPORT_NO_LOGS = False  # Turn on/off export of log-files

NUM_DISPATCHING_RULES = 6
NUM_MACHINES = 59
DISPATCHING_TYPE = "rule-free" # Options: "rule-free" or "rule-based"
MAINTENANCE_TYPE = "periodic" # Options: "periodic" or "job-based"

MIN_SIMULATION = 7*24


TIMESTEPS = 31
EPISODES = 100

PATH_TIME = "log/" + datetime.now().strftime("%Y%m%d_%H%M%S")

def define_production_parameters(episode):
    """
    Describe production system parameters
    """
    
    parameters = dict()
    parameters.update(({'SEED': 10}))
    random.seed(parameters['SEED'] + episode)
    parameters.update({"episodes": EPISODES})
    parameters.update({"timesteps": TIMESTEPS})

    parameters.update({'time_end': 0.0})
    
    parameters.update({'NUM_DISPATCHING_RULES': NUM_DISPATCHING_RULES})
    parameters.update({'DISPATCHING_TYPE': DISPATCHING_TYPE})
    parameters.update({'MAINTENANCE_TYPE': MAINTENANCE_TYPE})
    parameters.update({"MACHINES": []})
    parameters.update({"ORDERS": []})
    parameters.update({"NUM_ORDERS": []})



    parameters.update(({'EXPONENTIAL_SMOOTHING': 0.01}))  # Default: 0.01
    parameters.update(({'EPSILON': EPSILON}))
    parameters.update(({'PRINT_CONSOLE': PRINT_CONSOLE}))
    parameters.update(({'EXPORT_NO_LOGS': EXPORT_NO_LOGS}))
    

    parameters.update(({'PATH_TIME': PATH_TIME}))
    parameters.update(({'EXPORT_FREQUENCY': EXPORT_FREQUENCY}))



    # In this setting the RL-agent (TRPO-Algorithm) is controlling the transport decision making
    parameters.update({'AGENT_TYPE': "PPO"})  # Alternativen: TRPO, FIFO, NJF, EMPTY
    parameters.update({'AGENT_REWARD': "utilization"})  # Alternatives: valid_action, utilization, waiting_time_normalized, throughput, conwip, const_weighted, weighted_objectives
    parameters.update({'AGENT_REWARD_SPARSE': ""})  # Alternatives: valid_action, utilization, waiting_time
    parameters.update({'AGENT_REWARD_EPISODE_LIMIT': 0})  # Episode limit counter, default = 0
    parameters.update({'AGENT_REWARD_EPISODE_LIMIT_TYPE': "valid"})  # Alternatives: valid, entry, exit, time
    parameters.update({'AGENT_REWARD_SUBSET_WEIGHTS': [1.0, 1.0]})  # Standard: [1.0, 1.0]  |  First: Const weight values for action to machine, Second: weight for action to sink
    parameters.update({'AGENT_REWARD_OBJECTIVE_WEIGHTS': {'utilization': 1.0, 'waiting_time': 1.0}})
    
    parameters.update({"MIN_SIMULATION" : MIN_SIMULATION})
    
    # Number of machines in the 1st stage of the machine shop
    parameters.update({'NUM_MACHINES': NUM_MACHINES})
    parameters.update({"TERMINAL": False})



    return parameters

   

def define_production_statistics(parameters):
    """
    Statistics-Arrays for performance evaluation
    """
    statistics = dict()
    episode = dict()

    statistics.update({'machines_working': np.array([0.0] * parameters['NUM_MACHINES'])})
    statistics.update({'machines_broken': np.array([0.0] * parameters['NUM_MACHINES'])})
    statistics.update({'machines_idle': np.array([0.0] * parameters['NUM_MACHINES'])})
    statistics.update({'machines': [statistics['machines_working'],
                                    statistics['machines_broken'],
                                    statistics['machines_idle']]})

    statistics.update({'order_sop': defaultdict(int)})
    statistics.update({'order_eop': defaultdict(int)})
    statistics.update({'order_leadtime': defaultdict(int)})
    
    # States
    statistics.update({"broken_machines": 0})
    statistics.update({"preventive_maintenance" : 0})
    statistics.update({"delayed_orders": 0})
    statistics.update({"operating_machines": 0})
    statistics.update({"reward": 0})
    statistics.update({"num_setups": 0})
    statistics.update({"daily_production": 0})
    statistics.update({'products_arrivals': 0})
    
    statistics.update({"broken_machines_log": []})
    statistics.update({"delayed_orders_log": []})
    statistics.update({"operating_machines_log": []})
    statistics.update({"rewards_log": []})
    statistics.update({"preventive_maintenance_log": []})
    statistics.update({"num_setups_log": []})
    
    statistics.update({"broken_machines_EXPORT": []})
    statistics.update({"delayed_orders_EXPORT": []})
    statistics.update({"operating_machines_EXPORT": []})
    statistics.update({"rewards_EXPORT": []})
    statistics.update({"preventive_maintenance_EXPORT": []})
    statistics.update({"num_setups_EXPORT": []})
    statistics.update({"round_EXPORT": []})
    statistics.update({"daily_production_EXPORT": []})
    statistics.update({"episodes_counter_log": []})
    
    statistics.update({"NUM_ORDERS_log": []})
    statistics.update({"broken_reward": []})
    statistics.update({"productivity_reward": []})
    statistics.update({"operating_machines_reward": []})
    
    
    
    
    
    statistics.update({"mttr_log": {}})
    statistics.update({"mttf_log": {}})
    statistics.update({"remaining_usefull_life": {}})
    statistics.update({"num_processed_orders": []})
    
    


    statistics.update({'episode': [[0.0, 0]]})

    statistics.update({'agent_reward': [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]]})



    statistics.update({'sim_start_time': ""})
    statistics.update({'sim_end_time': ""})
    


    statistics.update({'orders_done': deque()})

    return statistics, episode