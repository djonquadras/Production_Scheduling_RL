# Libraries
import random
from collections import deque
import numpy as np
import pandas as pd
import progressbar
import statistics
import datetime as dt
from collections import Counter
from collections import defaultdict

# Parameters

# Extended print out during running, particularly for debugging
PRINT_CONS = False  

# Small number larger than zero used as "marginal" time step or to compare values
EPSILON = 0.000001

# Number of steps between csv-export of log-files
EXPORT_FREQ = 10 ** 3

# Turn on/off export of log-files
EXPORT_LOGS = False

# Seed
SEED = 10

# Path to export
PATH = "log/" + dt.now().strftime("%Y%m%d_%H%M%S")

# QUANTITY OF RESOURCES
MACHINES = 8  
SOURCES = 3
SINKS = 3

def def_Parameters(env, episode):
    """
    Describe production system parameters
    """
    parameters = defaultdict(int)
    parameters["SEED"] = SEED
    random.seed(parameters["SEED"] + episode)

    parameters["NUM_ORDERS"] = 10 ** 8  # Default: large number to not run out of orders

    parameters["time_end"] = 0.0

    parameters["stop_criteria"] = env.event()
    parameters["step_criteria"] = env.event()
    parameters["continue_criteria"] = env.event()

    parameters["EXPONENTIAL_SMOOTHING"] = 0.01
    parameters["EPSILON"] = EPSILON
    parameters["PRINT_CONS"] = PRINT_CONS
    parameters["EXPORT_LOGS"] = EXPORT_LOGS

    parameters["PATH"] = PATH
    parameters["EXPORT_FREQ"] = EXPORT_FREQ

    parameters["CHANGE_SCENARIO_AFTER_EPISODES"] = 5 * 10 ** 10

    # In this setting the RL-agent (TRPO-Algorithm) is controlling the transport decision making

    # Alternatives: TRPO, FIFO, NJF, EMPTY
    parameters["AGENT_TYPE"] = "TRPO"

    # Alternatives: valid_action, utilization, waiting_time_normalized, throughput, conwip, const_weighted, weighted_objectives
    parameters["REWARD"]= "utilization"
    
    # Alternatives: valid_action, utilization, waiting_time  
    parameters["REWARD_SPARSE"] = ""

    # Episode limit counter, default = 0
    parameters["REWARD_EPISODE_LIMIT"] = 0  

    # Alternatives: valid, entry, exit, time
    parameters["REWARD_EPISODE_LIMIT_TYPE"] = "valid"

    # Standard: [1.0, 1.0]  |  First: Const weight values for action to machine, Second: weight for action to sink
    parameters["REWARD_SUBSET_WEIGHTS"] = [1.0, 1.0]  
    parameters["REWARD_OBJECTIVE_WEIGHTS"] = {"utilization": 1.0, "waiting_time": 1.0}
    parameters["REWARD_WAITING_ACTION"] = 0.0
    parameters["REWARD_INVALID_ACTION"] = 0.0

    # Alternatives: True, False  
    parameters["WAITING_ACTION"] = False

    # Alternatives: True, False  
    parameters["EMPTY_ACTION"] = False

    # Number of machines in the machine shop  
    parameters["MACHINES"] = MACHINES  
    parameters["SOURCES"] = SOURCES
    parameters["SINKS"] = SINKS
    parameters["RESOURCES"] = parameters["MACHINES"] + parameters["SOURCES"] + parameters["SINKS"]
    parameters["PROD_VARIANTS"] = 1
    parameters["PROD_STEPS"] = 1

    # Source parameters
    parameters["SOURCE_CAPACITIES"] = [3] * parameters["SOURCES"]  # Number of load ports
    parameters["RESP_AREA_SOURCE"] = [[0, 1], [2, 3, 4], [5, 6, 7]]  # Orders for which machines are created in the specific source
    parameters["MTOG"] = [10.0, 10.0, 10.0]  # Mean Time Order Generation
    parameters["SOURCE_ORDER_GENERATION_TYPE"] = "ALWAYS_FILL_UP"  # Alternatives: ALWAYS_FILL_UP, MEAN_ARRIVAL_TIME

    # Machine parameters
    parameters["MACHINE_AGENT_TYPE"] = "FIFO"  # Alternatives: FIFO -> Decision rule for selecting the next available order from the load port
    parameters["MACHINE_GROUPS"] = [2, 1, 1, 1, 1, 3, 3, 3]

    parameters["MIN_PROCESS_TIME"] = [0.5] * parameters["MACHINES"]
    parameters["AVERAGE_PROCESS_TIME"] = [60.0] * parameters["MACHINES"]
    parameters["MAX_PROCESS_TIME"] = [150.0] * parameters["MACHINES"]
    parameters["CHANGEOVER_TIME"] = 0.0  # Default: Not used
    parameters["MTBF"] = [1000.0] * parameters["MACHINES"]  # Unscheduled breakdowns
    parameters["MTOL"] = [200.0] * parameters["MACHINES"]
    parameters["MACHINE_CAPACITIES"] = [6] * parameters["MACHINES"]  # Capacity for in and out machine buffers together

    # Order parameters
    parameters["ORDER_DISTRIBUTION"] = [1.0 / parameters["MACHINES"]] * parameters["MACHINES"]  # Probability which machine allocated, when orders are created
    parameters["VARIANT_DISTRIBUTION"] = [1.0 / parameters["NUM_PROD_VARIANTS"]] * parameters["NUM_PROD_VARIANTS"]  # Probability which product variant, when orders are created

    # Handling time
    parameters["TIME_TO_LOAD_MACHINE"] = 60.0 / 60.0
    parameters["TIME_TO_UNLOAD_MACHINE"] = 60.0 / 60.0
    parameters["TIME_TO_LOAD_SOURCE"] = 60.0 / 60.0
    parameters["TIME_TO_UNLOAD_SOURCE"] = 60.0 / 60.0

    # Transport time
    parameters["TRANSP_DISTANCE"] = [[50.0 for x in range(parameters["RESOURCES"])] for y in
                                       range(parameters["RESOURCES"])]
    parameters["TRANSP_TIME"] = [[0.0 for x in range(parameters["RESOURCES"])] for y in
                                       range(parameters["RESOURCES"])]
    for i in range(parameters["RESOURCES"]):
        for j in range(parameters["RESOURCES"]):
            parameters["TRANSP_TIME"][i][j] = parameters["TRANSP_DISTANCE"][i][j] / parameters["TRANSP_SPEED"]
            if i == j:
                parameters["TRANSP_TIME"][i][j] = 0.0
    parameters.update({"MAX_TRANSP_TIME": np.array(parameters["TRANSP_TIME"]).max()})

    return parameters
