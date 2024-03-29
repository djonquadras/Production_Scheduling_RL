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
NUM_MACHINES_1_STAGE = 59
NUM_MACHINES_2_STAGE = 3
NUM_MACHINES_3_STAGE = 4
TIPO_DISPATCHING = "rule-free" # Options: "rule-free" or "rule-based"
TIPO_MANUTENCAO = "periodic" # Options: "periodic" or "job-based"

MIN_SIMULATION = 720
EPISODES = 1000


PATH_TIME = "log/" + datetime.now().strftime("%Y%m%d_%H%M%S")

def define_production_parameters(episode):
    """
    Describe production system parameters
    """
    
    parameters = dict()
    parameters.update(({'SEED': 10}))
    random.seed(parameters['SEED'] + episode)
    parameters.update({"episodes": EPISODES})

    parameters.update({'time_end': 0.0})
    
    parameters.update({'NUM_DISPATCHING_RULES': NUM_DISPATCHING_RULES})
    parameters.update({'TIPO_DISPATCHING': TIPO_DISPATCHING})
    parameters.update({'TIPO_MANUTENCAO': TIPO_MANUTENCAO})
    parameters.update({"MACHINES": []})



    parameters.update(({'EXPONENTIAL_SMOOTHING': 0.01}))  # Default: 0.01
    parameters.update(({'EPSILON': EPSILON}))
    parameters.update(({'PRINT_CONSOLE': PRINT_CONSOLE}))
    parameters.update(({'EXPORT_NO_LOGS': EXPORT_NO_LOGS}))
    

    parameters.update(({'PATH_TIME': PATH_TIME}))
    parameters.update(({'EXPORT_FREQUENCY': EXPORT_FREQUENCY}))



    # In this setting the RL-agent (TRPO-Algorithm) is controlling the transport decision making
    parameters.update({'AGENT_TYPE': "TRPO"})  # Alternativen: TRPO, FIFO, NJF, EMPTY
    parameters.update({'AGENT_REWARD': "utilization"})  # Alternatives: valid_action, utilization, waiting_time_normalized, throughput, conwip, const_weighted, weighted_objectives
    parameters.update({'AGENT_REWARD_SPARSE': ""})  # Alternatives: valid_action, utilization, waiting_time
    parameters.update({'AGENT_REWARD_EPISODE_LIMIT': 0})  # Episode limit counter, default = 0
    parameters.update({'AGENT_REWARD_EPISODE_LIMIT_TYPE': "valid"})  # Alternatives: valid, entry, exit, time
    parameters.update({'AGENT_REWARD_SUBSET_WEIGHTS': [1.0, 1.0]})  # Standard: [1.0, 1.0]  |  First: Const weight values for action to machine, Second: weight for action to sink
    parameters.update({'AGENT_REWARD_OBJECTIVE_WEIGHTS': {'utilization': 1.0, 'waiting_time': 1.0}})
    
    parameters.update({"MIN_SIMULATION" : MIN_SIMULATION})
    
    # Number of machines in the 1st stage of the machine shop
    parameters.update({'NUM_MACHINES_1_STAGE': NUM_MACHINES_1_STAGE})
    
    # Number of machines in the 2nd stage of the machine shop  
    parameters.update({'NUM_MACHINES_2_STAGE':  NUM_MACHINES_2_STAGE})
    
    # Number of machines in the 3rd stage of the machine shop  
    parameters.update({'NUM_MACHINES_3_STAGE':  NUM_MACHINES_3_STAGE})
    parameters.update({"NUM_MACHINES": NUM_MACHINES_1_STAGE + NUM_MACHINES_2_STAGE + NUM_MACHINES_3_STAGE})  
    
    # Total number of machines in the machine shop
    parameters.update({'NUM_MACHINES': parameters['NUM_MACHINES_1_STAGE'] + parameters['NUM_MACHINES_2_STAGE'] + parameters['NUM_MACHINES_3_STAGE']})

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
    statistics.update({"maquinas_ocupadas": 0})
    statistics.update({"reward": 0})
    
    statistics.update({"broken_machines_log": []})
    statistics.update({"delayed_orders_log": []})
    statistics.update({"maquinas_ocupadas_log": []})
    statistics.update({"rewards_log": []})
    statistics.update({"preventive_maintenance_log": []})
    
    


    statistics.update({'episode': [[0.0, 0]]})

    statistics.update({'agent_reward': [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]]})



    statistics.update({'sim_start_time': ""})
    statistics.update({'sim_end_time': ""})
    


    statistics.update({'orders_done': deque()})

    return statistics, episode