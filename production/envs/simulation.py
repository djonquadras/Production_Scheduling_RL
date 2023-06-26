import sys
from tensorforce.environments import Environment
import numpy as np
from production.envs.initialize_env import define_production_parameters
from production.envs.initialize_env import define_production_statistics
import logging
from production.envs.machine import Machines
from production.envs.weibull import weibull
from production.envs.order import Order
from datetime import datetime
import simpy
from statistics import mean 
import pandas as pd

'''
Função para simular o sistema produtivo
'''
class ProductionEnv(Environment):
    
    def __init__(self):
        
        super().__init__()
        self.count_episode = 0

        # Cria a variável que será o ambiente e seus parâmetros
        self.env = simpy.Environment()
        self.counter = 0
        self.in_reset = False
        self.list_machines = []
        self.list_ordens = []
        
        self.dataset_ordens = pd.read_excel('inputs/dataset_ordens.xlsx')
        self.dataset_machines = pd.read_excel('inputs/dataset_maquinas.xlsx')
        self.quebra_machines = []
        for i in self.dataset_machines["id_machine"]:
            self.quebra_machines.append(weibull(10,144))
        
        # Define os parâmetros de toda a simulação
        self.parameters = define_production_parameters(episode = self.count_episode)
        self.parameters.update({'num_orders': self.dataset_ordens.shape[0]})
        self.parameters.update({'num_machines': self.dataset_machines.shape[0]})
        
        # Define as estatísticas de toda a simulação
        self.statistics, self.stat_episode = define_production_statistics(parameters=self.parameters)
        
        for i in self.dataset_machines["id_machine"]:
            self.statistics["mttr_log"].update({i: []})
            self.statistics["mttf_log"].update({i: []})
            

    '''
    Generate machines in the production system
    '''
        
    def generate_machines(self, actions):
        
        
        id_machine = self.dataset_machines["id_machine"]
        corrective_time = self.dataset_machines["corrective_time"]
        preventive_time = self.dataset_machines["preventive_time"]
        usefull_time = self.dataset_machines["usefull_time"]
        
        
        dispatching_rule = []
        if self.parameters["DISPATCHING_TYPE"] == "rule-based":
            dispatching_rule = actions["DR_machines"]
        else:
            dispatching_rule = [0]*self.parameters['NUM_MACHINES']
        
        if self.parameters["MAINTENANCE_TYPE"] == "periodic":
            maintenance_period = actions["maintenance_period"]
        else:
            maintenance_period = [0]*self.parameters["NUM_MACHINES"]
        
        
        for index, machine in enumerate(id_machine):
            
            self.list_machines.append(Machines(env = self.env,
                                                id_machine = machine,
                                                statistics = self.statistics,
                                                parameters = self.parameters,
                                                usefull_time = usefull_time[index],
                                                preventive_time = preventive_time[index],
                                                corrective_time = corrective_time[index],
                                                machine_env = simpy.PriorityResource(self.env),
                                                maintenance_period = int(maintenance_period[index]),
                                                dispatching_rule = dispatching_rule[index]))
        
        self.parameters["MACHINES"] = self.list_machines
          
    '''
    Generates the state set for the agent
    '''
    def gen_states(self):

        preventives = []
        correctives = []
        mttr = []
        mttf = []


        if len(self.statistics["broken_machines_log"]) == 0:
            preventives = [0]
            correctives = [0]
            mttr = [0]*self.parameters["NUM_MACHINES"]
            mttf = [0]*self.parameters["NUM_MACHINES"]

            delayed_orders = [0]
        
        else:

            correctives = [self.statistics["broken_machines"]]
            preventives = [self.statistics["preventive_maintenance"]]
            delayed_orders = [self.statistics["delayed_orders"]]
            
            for maq in self.list_machines:
                maq.calc_MTTR()
                maq.calc_MTTF()
                mttr.append(mean(self.statistics["mttr_log"][maq.id_machine]))
                mttf.append(mean(self.statistics["mttf_log"][maq.id_machine]))

        

        operating_machines = [float(self.statistics["operating_machines"])]
        

        states = np.concatenate([operating_machines,
                                 preventives,
                                 correctives,
                                 mttf,
                                 mttr,
                                 delayed_orders])

        
        return states


    '''
    Extort states to log 
    '''
    def export_states(self):
                
        preventives = []
        correctives = []
        mttr = []
        mttf = []


        if len(self.statistics["broken_machines_log"]) == 0:
            preventives = [0]
            correctives = [0]
            mttr = [0]*self.parameters["NUM_MACHINES"]
            mttf = [0]*self.parameters["NUM_MACHINES"]

            delayed_orders = [0]
        
        else:
            
            correctives = [self.statistics["broken_machines"]]
            preventives = [self.statistics["preventive_maintenance"]]
            delayed_orders = [self.statistics["delayed_orders"]]
            
            for maq in self.list_machines:
                maq.calc_MTTR()
                maq.calc_MTTF()
                mttr.append(mean(self.statistics["mttr_log"][maq.id_machine]))
                mttf.append(mean(self.statistics["mttf_log"][maq.id_machine]))

        

        operating_machines = [float(self.statistics["operating_machines"])]
        
        logging.info(f"Correctives = {correctives}")
        logging.info(f"Preventives = {preventives}")
        logging.info(f"Delayed Orders = {delayed_orders}")
        logging.info(f"Operating Machines = {operating_machines}")
        #logging.info(f"MTTR = {mttr}")
        #logging.info(f"MTTF = {mttf}")

        
    
    '''
    Generate jobs for the production system
    '''
    def generate_jobs(self, actions):
        
        # Parameters from excel file
        id_material = self.dataset_ordens["id_material"]
        material_type = self.dataset_ordens["material_type"]
        processing_time = self.dataset_ordens["processing_time"]
        due_date = self.dataset_ordens["due_date"]

        # Parameters from agent actions

        machine = []
        priority = []
        operating_machines = 0
        
        if self.parameters["DISPATCHING_TYPE"] == "rule-free":
            priority = actions["priorities"]
            machine = actions["machine_selection"]
            operating_machines = len(pd.DataFrame({"b": actions["machine_selection"]})["b"].unique())
        else:        
            operating_machines = actions["Operating_Machines"][0]
            machine = [operating_machines]*self.parameters["num_orders"]
            priority = [operating_machines]*self.parameters["num_orders"]

            
        # For job-based maintenance
        job_preventive_list = [False] * self.parameters["num_orders"]
        
        if self.parameters["MAINTENANCE_TYPE"] == "job-based":
            job_preventive_list = actions["prev_maint_job"]
            
                    
        self.statistics["operating_machines"] = operating_machines
        
        for index, ordem in enumerate(id_material):
            
            self.list_ordens.append(Order(self.env,
                                           id_material = ordem,
                                           material_type = material_type[index],
                                           processing_time = processing_time[index],
                                           machine = machine[index],
                                           priority = priority[index],
                                           due_date = due_date[index],
                                           statistics = self.statistics,
                                           parameters= self.parameters,
                                           maintenance_job_based = job_preventive_list[index]))
            
        
    def states(self):
        number = 0
        
        # Number of operation machines
        number += 1
        
        # Number of Preventives
        number += 1
        
        # Number of correctives 
        number += 1
        
        # Number of Setups
        #number += 1
        
        # Number of jobs for each machine 
        #number += self.parameters["NUM_MACHINES"]
        
        # MTTF for each machine
        number += self.parameters["NUM_MACHINES"]
        
        # MTTR for each machine
        number += self.parameters["NUM_MACHINES"]
        
        # Number of delayed jobs 
        number += 1

        
        return {"type":'float',
                "shape": number}
    
    # Optional additional steps to close environment
    def close(self):
        super().close()

    def reset(self):


        self.statistics["broken_machines_log"] = []
        self.statistics["delayed_orders_log"] = []
        self.statistics["operating_machines_log"] = []
        self.statistics["rewards_log"] = []
        self.statistics["preventive_maintenance_log"] = []
        self.statistics["num_setups_log"] = []
        self.statistics["mttr_log"] = {}
        self.statistics["mttf_log"] = {}
        for i in self.dataset_machines["id_machine"]:
            self.statistics["mttr_log"].update({i: []})
            self.statistics["mttf_log"].update({i: []})
        self.statistics["num_processed_orders"] = []
        self.counter = 0
        self.in_reset = True
        states = self.gen_states()
        self.in_reset = False
        return states
    
    def reset_states(self):
        self.statistics["broken_machines"] = 0
        self.statistics["delayed_orders"] = 0
        self.statistics["operating_machines"] = 0
        self.statistics["reward"] = 0
        self.statistics["preventive_maintenance"] = 0
        
    def update_log(self):
        self.statistics["broken_machines_log"].append(self.statistics["broken_machines"])
        self.statistics["delayed_orders_log"].append(self.statistics["delayed_orders"])
        self.statistics["operating_machines_log"].append(self.statistics["operating_machines"])
        self.statistics["rewards_log"].append(self.statistics["reward"])
        self.statistics["preventive_maintenance_log"].append(self.statistics["preventive_maintenance"])
        self.statistics["num_setups_log"].append(self.statistics["num_setups"])
            
    def gen_reward(self):
        reward = 0
        reward += -3*self.statistics["broken_machines"]
        reward += -3*self.statistics["delayed_orders"]
        reward += -1*self.statistics["operating_machines"]
        reward += -1*self.statistics["preventive_maintenance"]
        self.statistics["reward"] = reward
        return reward
    
    def execute(self, actions):

        print(f"<------------------------ Start {self.counter} ------------------------>")
        logging.info(f"Current Reward = {self.statistics['reward']}")
        self.export_states()
        
        
        reward = None
        terminal = False
        states = None
        self.counter += 1
        
        self.reset_states()
        
        # Rebooting environment         
        self.env = simpy.Environment()

        self.list_machines = []
        self.list_ordens = []
        self.generate_machines(actions)
        self.generate_jobs(actions)
        
    
        
        
        self.env.run(until = self.parameters["MIN_SIMULATION"])
        
        delayed = 0
        finished = 0
        
        for order in self.list_ordens:
            if order.finished == False:
                delayed +=1
            else:
                finished += 1
        
        print(f"Total = {delayed + finished} | Delayed = {delayed} | Finished = {finished}")
        self.statistics["delayed_orders"] = delayed


        reward = self.gen_reward()
        self.update_log()
        states = self.gen_states()

        
        if self.counter == self.parameters["episodes"]:
            terminal = True
         
            for machine in self.list_machines:
                logging.info(f" Machine {machine.id_machine} = {machine.production_sequence}")
                logging.info("")
            
            logging.info("")
            logging.info("")
            logging.info("Broken Machines")    
            logging.info(self.statistics["broken_machines_log"])
            logging.info("")
            logging.info("Delayed Orders")    
            logging.info(self.statistics["delayed_orders_log"])
            logging.info("")
            logging.info("Operating Machines")    
            logging.info(self.statistics["operating_machines_log"])
            logging.info("")
            logging.info("Preventive Performed")    
            logging.info(self.statistics["preventive_maintenance_log"])
            logging.info("")
            logging.info("Rewards")    
            logging.info(self.statistics["rewards_log"])
            

        #print("<------------------------ End ------------------------>")        
        
        

            
        if terminal:    
            self.parameters.update({"ACTION": actions})
            

     
        
        
        return states, terminal, reward




    def actions(self):
        

        actions = {}
        
        # Se o tipo de Dispatching for "rule-based"
        if self.parameters["DISPATCHING_TYPE"] == "rule-based":
            
            # Seleciona as regras de despacho para as máquinas
            actions.update({"DR_machines": {"type":'int',
                                            "shape": self.parameters['NUM_MACHINES'],
                                            "num_values": self.parameters['NUM_DISPATCHING_RULES']}})

            
            # Determina a quantidade de máquinas operando no primeiro estágio
            actions.update({"Operating_Machines": {"type":'int',
                                                   "shape": 1,
                                                   "num_values": self.parameters['NUM_MACHINES']}})
            
        
        # Se o tipo de Dispatching for "rule-free"
        else:
            
            # Select the machine that will produce each job
            actions.update({"machine_selection": {"type":'int',
                                                  "shape": self.parameters["num_orders"],
                                                  "num_values": self.parameters['NUM_MACHINES']}})


            
            # Determine job priority        
            actions.update({"priorities":  {"type":'float',
                                             "shape": self.parameters["num_orders"]}})

        
        # For job-Based Maintenance
        if self.parameters["MAINTENANCE_TYPE"] == "job-based":
            
            actions.update({"prev_maint_job": {"type":'bool',
                                               "shape": self.parameters["num_orders"]}})
        
        else: 
        
            actions.update({"maintenance_period":   {"type":'int',
                                                    "num_values": 45*24,
                                                    "shape": self.parameters["num_machines"]}})

        return actions
    
