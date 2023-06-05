from collections import defaultdict
import numpy as np

# Define Production Statistics
def def_Statistics(parameters):
    """
    Statistic-Arrays for performance evaluation
    """
    statistics = defaultdict(int)
    stat_episode = defaultdict(int)

    statistics["working"] = np.array([0.0] * parameters["NUM_MACHINES"])
    statistics["broken"] = np.array([0.0] * parameters["NUM_MACHINES"])
    statistics["idle"] = np.array([0.0] * parameters["NUM_MACHINES"])
    statistics["changeover"] = np.array([0.0] * parameters["NUM_MACHINES"])
    statistics["machines_processed_orders"] = np.array([0.0] * parameters["NUM_MACHINES"])
    statistics["machines"]= [statistics["working"],
                             statistics["broken"],
                             statistics["idle"],
                             statistics["changeover"]]

    statistics["transp_working"] = np.array([0.0] * parameters["NUM_TRANSP_AGENTS"])
    statistics["transp_walking"] = np.array([0.0] * parameters["NUM_TRANSP_AGENTS"])
    statistics["transp_handling"] = np.array([0.0] * parameters["NUM_TRANSP_AGENTS"])
    statistics["transp_idle"] = np.array([0.0] * parameters["NUM_TRANSP_AGENTS"])
    statistics["transp"] = [statistics["transp_walking"],
                            statistics["transp_idle"]]
    statistics["transp_selected_idle"] = np.array([0] * parameters["NUM_TRANSP_AGENTS"])
    statistics["transp_forced_idle"] = np.array([0] * parameters["NUM_TRANSP_AGENTS"])
    statistics["transp_threshold_waiting_reached"] = np.array([0] * parameters["NUM_TRANSP_AGENTS"])

    statistics["order_sop"] = defaultdict(int)
    statistics["order_eop"] = defaultdict(int)
    statistics["order_waiting"] = defaultdict(int)
    statistics["order_processing"] = defaultdict(int)
    statistics["order_handling"] = defaultdict(int)
    statistics["order_leadtime"] = defaultdict(int)

    statistics["order"] = [statistics["order_sop"],
                           statistics["order_eop"],
                           statistics["order_waiting"],
                           statistics["order_processing"],
                           statistics["order_handling"],
                           statistics["order_leadtime"]]

    statistics["inv_buffer_in"] = np.array([0.0] * parameters["NUM_RESOURCES"])
    statistics["inv_buffer_out"] = np.array([0.0] * parameters["NUM_RESOURCES"])
    statistics["inv_buffer_in_mean"]= [np.array([0.0] * parameters["NUM_RESOURCES"]),
                                            np.array([0.0] * parameters["NUM_RESOURCES"])]
    statistics["inv_buffer_out_mean"]=  [np.array([0.0] * parameters["NUM_RESOURCES"]),
                                         np.array([0.0] * parameters["NUM_RESOURCES"])]
    statistics["inv"]=  [statistics["inv_buffer_in"],
                         statistics["inv_buffer_out"]]
    statistics["inv_episode"] = [[0.0, 0]]

    statistics["agent_reward"] = [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]]

    statistics["agent_reward_log"] = open(parameters["PATH_TIME"] + "_agent_reward_log.txt", "w")
    statistics["episode_log"] = open(parameters["PATH_TIME"] + "_episode_log.txt", "w")
    statistics["episode_statistics"] = ["machines_working",
                                        "machines_changeover",
                                        "machines_broken",
                                        "machines_idle",
                                        "machines_processed_orders",
                                        "transp_working",
                                        "transp_walking",
                                        "transp_handling",
                                        "transp_idle"]

    statistics["sim_start_time"] = ""
    statistics["sim_end_time"] = ""

    statistics["prefilled_orders"] = ""

    # Episode KPI Logger
    statistics["episode_log_header"] = ["episode_counter",
                                        "sim_step",
                                        "sim_time",
                                        "dt",
                                        "dt_real_time",
                                        "valid_actions",
                                        "total_reward",
                                        "machines_working",
                                        "machines_changeover",
                                        "machines_broken",
                                        "machines_idle",
                                        "processed_orders",
                                        "transp_working",
                                        "transp_walking",
                                        "transp_handling",
                                        "transp_idle",
                                        "machines_total",
                                        "selected_idle",
                                        "forced_idle",
                                        "threshold_waiting",
                                        "finished_orders",
                                        "order_waiting_time",
                                        "alpha",
                                        "inventory"]
    string = ""
    for x in statistics["episode_log_header"]:
        string = string + x + ","
    string = string[:-1]
    statistics["episode_log"].write("%s\n" % (string))

    # Reward Agent Logger
    string = "episode,sim_step,sim_time,action,reward,action_valid,state"
    statistics["agent_reward_log"].write("%s\n" % (string))
    statistics["agent_reward_log"].close()

    # Temp statistics
    for stat in statistics["episode_statistics"]:
        stat_episode.update({stat: np.array([0.0] * len(statistics[stat]))})

    statistics.update({"orders_done": deque()})

    return statistics, stat_episode

def define_production_resources(env, statistics, parameters, agents, time_calc):
    resources = dict()

    # Create an environment and start the setup process
    resources["machines"] = [Machine(env = env,
                                     id = i,
                                     capacity = parameters["MACHINE_CAPACITIES"][i],
                                     agent_type = parameters["MACHINE_AGENT_TYPE"],
                                     machine_group = parameters["MACHINE_GROUPS"][i],
                                     statistics = statistics,
                                     parameters = parameters,
                                     resources = resources,
                                     agents = agents,
                                     time_calc = time_calc,
                                     location = None,
                                     label = None) for i in range(parameters["NUM_MACHINES"])]
    resources["sources"] =  [Source(env=env,
                                    id=i + parameters["NUM_MACHINES"],
                                    capacity=parameters["SOURCE_CAPACITIES"][i],
                                    resp_area=parameters["RESP_AREA_SOURCE"][i],
                                    statistics=statistics,
                                    parameters=parameters,
                                    resources=resources,
                                    agents=agents,
                                    time_calc=time_calc,
                                    location=None,
                                    label=None) for i in range(parameters["NUM_SOURCES"])]
    resources["sinks"] =    [Sink(env = env,
                                  id = i + parameters["NUM_MACHINES"] + parameters["NUM_SOURCES"],
                                  statistics = statistics,
                                  parameters = parameters,
                                  resources = resources,
                                  agents = agents,
                                  time_calc = time_calc,
                                  location = None,
                                  label = None) for i in range(parameters["NUM_SINKS"])]

    temp_resources = []
    temp_resources.extend(resources["machines"])
    temp_resources.extend(resources["sources"])
    temp_resources.extend(resources["sinks"])

    resources["all_resources"] = temp_resources

    resources["transps"] =  [Transport( env = env,
                                        id = i,
                                        resp_area = parameters["RESP_AREA_TRANSP"][i],
                                        agent_type = parameters["TRANSP_AGENT_TYPE"],
                                        statistics = statistics,
                                        parameters = parameters,
                                        resources = resources,
                                        agents = agents,
                                        time_calc = time_calc,
                                        location = None,
                                        label = None) for i in range(parameters["NUM_TRANSP_AGENTS"])]

    resources["repairman"] = simpy.PreemptiveResource(env, capacity=parameters["NUM_MACHINES"])

    env.process(other_jobs(env, resources["repairman"]))

    # Create source and machine normalizers
    source_wt_normalizer = ZScoreNormalization("exp", alpha=0.01)
    machine_wt_normalizer = ZScoreNormalization("exp", alpha=0.01)
    for mach in resources["machines"]:
        mach.machine_wt_normalizer = machine_wt_normalizer
    for sourc in resources["sources"]:
        sourc.source_wt_normalizer = source_wt_normalizer

    print("All resources types: ", [x.type for x in resources["all_resources"]])
    print("All resources ids: ", [x.id for x in resources["all_resources"]])
    print("Number of machines: ", len(resources["machines"]))
    print("Number of sources: ", len(resources["sources"]))
    print("Number of sinks: ", len(resources["sinks"]))

    return resources