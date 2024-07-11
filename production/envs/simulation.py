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
from datetime import datetime


class ProductionEnv(Environment):
    
    def __init__(self):
        
        super().__init__()
        self.count_episode = 0


        self.env = simpy.Environment()
        self.counter = 0
        self.episodes_counter = 0
        self.episodes = 0
        self.in_reset = False
        self.list_machines = []
        
        self.dataset_ordens = pd.read_excel('inputs/dataset_ordens.xlsx')
        self.dataset_machines = pd.read_excel('inputs/dataset_maquinas.xlsx')
        

        self.parameters = define_production_parameters(episode = self.count_episode)
        self.parameters.update({'num_orders': self.dataset_ordens.shape[0]})
        self.parameters.update({'num_machines': self.dataset_machines.shape[0]})
        
        self.statistics, self.stat_episode = define_production_statistics(parameters=self.parameters)
        
        for i in self.dataset_machines["id_machine"]:
            self.statistics["mttr_log"].update({i: []})
            self.statistics["mttf_log"].update({i: []})
            self.statistics["remaining_usefull_life"].update({i: []})
        
        self.generate_machines()
        self.orders = []


    def gen_states(self):

      
        state = []


        if len(self.statistics["broken_machines_log"]) == 0:
            
            state = [0]*(self.parameters["NUM_MACHINES"]+6)
        
        else:
            
            state.append(self.statistics["broken_machines"])
            state.append(self.statistics["preventive_maintenance"])
            state.append(self.statistics["delayed_orders"])
            state.append(self.statistics['daily_production'])
            state.append(self.counter)
            state.append(len(self.parameters["ORDERS"]))
            
            for maq in self.list_machines:
                state.append(maq.remaining_usefull_life)

        state.append(float(self.statistics["operating_machines"]))
        
        return state



    def export_states(self):
                
        operating_machines = float(self.statistics["operating_machines"])
        correctives = self.statistics["broken_machines"]
        preventives = self.statistics["preventive_maintenance"]
        delayed_orders = self.statistics["delayed_orders"]     


        logging.info("Timesteps states")
        logging.info(f"Correctives = {correctives}")
        logging.info(f"Preventives = {preventives}")
        logging.info(f"Delayed Orders = {delayed_orders}")
        logging.info(f"Operating Machines = {operating_machines}")


       
    def generate_jobs(self):
        
        
        ordens_criadas_agora = 0
        ordens_para_criar = 0
        id_material = self.dataset_ordens["id_material"]
        material_type = self.dataset_ordens["material_type"]
        processing_time = self.dataset_ordens["processing_time"]
        due_date = self.dataset_ordens["due_date"]
        start_date = self.dataset_ordens["start_date"]
        
        self.orders = []
        
        for index, ordem in enumerate(id_material):
            
            if start_date[index] == 0:
                ordens_criadas_agora += 1
                self.parameters["ORDERS"].append(Order(self.env,
                                            id_material = ordem,
                                            material_type = material_type[index],
                                            processing_time = processing_time[index],
                                            start_date = start_date[index],
                                            parameters = self.parameters,
                                            statistics = self.statistics,
                                            due_date = due_date[index]))
            else:
                ordens_para_criar += 1    
                self.orders.append(Order(self.env,
                                            id_material = ordem,
                                            material_type = material_type[index],
                                            processing_time = processing_time[index],
                                            start_date = start_date[index],
                                            statistics = self.statistics,
                                            parameters = self.parameters,
                                            due_date = due_date[index]))
        
            
        
    def states(self):
        number = 0
        
        # Number of operation machines
        number += 1
        
        # Number of Preventives
        number += 1
        
        # Number of correctives 
        number += 1
        
        # Remaining Usefull Life 
        number += self.parameters["NUM_MACHINES"]
        
        # Number of produced Orders 
        number += 1
        
        # Number of delayed jobs 
        number += 1

        # Counter 
        number += 1
        
        # Number of backlog orders
        number += 1

        
        return {"type":'float',
                "shape": number}
    
    # Optional additional steps to close environment
    def close(self):
        super().close()

    def reset(self):

        self.episodes += 1
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
        
        
        self.env = simpy.Environment()
        self.parameters["ORDERS"] = []
        
        
        for machine in self.parameters["MACHINES"]:
            machine.env = self.env
            machine.machine_env = simpy.PriorityResource(self.env)
            self.env.process(machine.execute())
        
        return states
    
    def reset_states(self):
        self.statistics["broken_machines"] = 0
        self.statistics["delayed_orders"] = 0
        self.statistics["operating_machines"] = 0
        self.statistics["reward"] = 0
        self.statistics["preventive_maintenance"] = 0
        self.statistics['daily_production'] = 0
        self.statistics['products_arrivals'] = 0
        self.statistics["NUM_ORDERS"] = 0
        self.statistics["num_setups"] = 0
    
        
    def update_log(self):
        self.statistics["broken_machines_log"].append(self.statistics["broken_machines"])
        self.statistics["delayed_orders_log"].append(self.statistics['delayed_orders'])
        self.statistics["operating_machines_log"].append(self.statistics["operating_machines"])
        self.statistics["rewards_log"].append(self.statistics["reward"])
        self.statistics["preventive_maintenance_log"].append(self.statistics["preventive_maintenance"])
        self.statistics["num_setups_log"].append(self.statistics["num_setups"])
        self.statistics["round_EXPORT"].append(f"Round {self.episodes_counter}")
        self.statistics["operating_machines_EXPORT"].append(self.statistics["operating_machines"])
        self.statistics["broken_machines_EXPORT"].append(self.statistics["broken_machines"])
        self.statistics["preventive_maintenance_EXPORT"].append(self.statistics["preventive_maintenance"])
        self.statistics["num_setups_EXPORT"].append(self.statistics["num_setups"])
        self.statistics["delayed_orders_EXPORT"].append(self.statistics['delayed_orders'])
        self.statistics["rewards_EXPORT"].append(self.statistics["reward"])
        self.statistics["daily_production_EXPORT"].append(self.statistics["daily_production"])
        self.statistics["episodes_counter_log"].append(self.episodes)
        
        self.statistics["NUM_ORDERS_log"].append(self.statistics["NUM_ORDERS"])
        self.statistics["broken_reward"].append(self.normilize_broken())
        self.statistics["productivity_reward"].append(self.normilize_productivity())        
        self.statistics["operating_machines_reward"].append(self.normilize_operating_machines())

        
    def calculate_delayed_orders(self):
        delayed = 0
        for order in self.parameters["ORDERS"]:
            if order.due_date < self.env.now:
                delayed += 1
        self.statistics["delayed_orders"] = delayed
        
    def normilize_productivity(self):
        
        qnt = self.statistics['daily_production']
        max = self.statistics["NUM_ORDERS"]
        
        if max == 0:
            return 0
        
        return qnt/max
    
    def normilize_operating_machines(self):
        a = self.parameters['NUM_MACHINES']
        x = self.statistics["operating_machines"]
        
        return (-1*x/a) +1

    def normilize_broken(self):
        a = self.parameters['NUM_MACHINES']
        x = self.statistics["broken_machines"]
        
        return (-1*x/a) +1


    def normilize_maintenance(self):
        a = self.parameters['NUM_MACHINES']
        x = self.statistics["preventive_maintenance"]
        
        return (-1*x/a) +1

            
    def gen_reward(self):
        reward = 0
        #reward += self.parameters['NUM_MACHINES'] -2*self.statistics["broken_machines"] -1*self.statistics["preventive_maintenance"]
        reward += 0.2*self.normilize_broken()
        reward += 0.4*self.normilize_productivity()
        reward += 0.4*self.normilize_operating_machines()
        self.statistics["reward"] = reward
        return reward
    
    def execute(self, actions):

        #print(f"<------------------------ Start {self.counter} ------------------------>")
        
        
        
        self.reset_states()
        
        reward = None
        terminal = False
        states = None
        self.counter += 1
        self.episodes_counter += 1
        
        
        if self.counter == 1:
            self.generate_jobs()
        
        
        
    
        
        self.set_DR(actions)

        for machine in self.parameters["MACHINES"]:
            if machine.turned_off:
                self.env.process(machine.execute())

        for machine in self.parameters["MACHINES"]:
            machine.production_sequence.append(f"DIA {self.counter}")
    
        
        self.env.run(until = 24*(self.counter))
        
        self.statistics["NUM_ORDERS"] = len(self.parameters['ORDERS']) + self.statistics['daily_production']

        
        #print(f"Ordens Produzidas no dia = {self.statistics['daily_production']}")
        #print(f"Job Arrivals = {self.statistics['products_arrivals']}")
        #print(f"Quantidade de Ordens de Produção DEPOIS de processar = {len(self.parameters['ORDERS'])}")
        
        #self.calculate_delayed_orders()
        #self.export_states()
        


        reward = self.gen_reward()
        states = self.gen_states()
        self.update_log()
        #logging.info(f"Current Reward = {self.statistics['reward']}")
        #logging.info(f"Equação: = {self.statistics['reward']}")
        #logging.info(f"self.parameters['NUM_MACHINES'] -3*self.statistics['broken_machines'] -1*self.statistics['preventive_maintenance'] = {self.parameters['NUM_MACHINES']} -3*{self.statistics['broken_machines']} -1*{self.statistics['preventive_maintenance']} = {self.parameters['NUM_MACHINES'] -3*self.statistics['broken_machines'] -1*self.statistics['preventive_maintenance']}")
        #logging.info(f"-3*self.statistics['delayed_orders'] = -3*{self.statistics['delayed_orders']} = {-3*self.statistics['delayed_orders']}")
        #logging.info(f"self.parameters['NUM_MACHINES'] -1*self.statistics['operating_machines'] = {self.parameters['NUM_MACHINES']} -1*{self.statistics['operating_machines']} = {self.parameters['NUM_MACHINES'] -1*self.statistics['operating_machines'] }")
        
        
        if self.counter == self.parameters["timesteps"]:
            terminal = True
         
            #for machine in self.list_machines:
            #    logging.info(f" Machine {machine.id_machine} = {machine.production_sequence}")
            #    logging.info("")
            
            #logging.info("")
            #logging.info("")
            #logging.info("Broken Machines")    
            #logging.info(self.statistics["broken_machines_log"])
            #logging.info("")
            #logging.info("Delayed Orders")    
            #logging.info(self.statistics["delayed_orders_log"])
            #logging.info("")
            #logging.info("Operating Machines")    
            #logging.info(self.statistics["operating_machines_log"])
            #logging.info("")
            #logging.info("Preventive Performed")    
            #logging.info(self.statistics["preventive_maintenance_log"])
            #logging.info("")
            #logging.info("Rewards")    
            #logging.info(self.statistics["rewards_log"])
            

        #print("<------------------------ End ------------------------>")        
        
        

            
        if terminal:    
            self.parameters.update({"ACTION": actions})
            

     
        if self.episodes_counter == self.parameters["episodes"]*self.parameters["timesteps"]:
        
            export_dataset = {"Round" : self.statistics["round_EXPORT"],
                              "Episode": self.statistics["episodes_counter_log"],
                              "Operating Machines": self.statistics["operating_machines_EXPORT"],
                              "Broken Machines": self.statistics["broken_machines_EXPORT"],
                              "Preventive Maintenance": self.statistics["preventive_maintenance_EXPORT"],
                              "Setups": self.statistics["num_setups_EXPORT"],
                              "Produced Orders": self.statistics["daily_production_EXPORT"],
                              "Delayed Orders": self.statistics["delayed_orders_EXPORT"],
                              "Number of available orders": self.statistics["NUM_ORDERS_log"],
                              "Broken Machines Reward 0.2": self.statistics["broken_reward"],
                              "Productivity Reward 0.4": self.statistics["productivity_reward"],
                              "Operating Machine Reward 0.4": self.statistics["operating_machines_reward"],
                              "Reward": self.statistics["rewards_EXPORT"]}
            
            export_dataset = pd.DataFrame(export_dataset)
            export_dataset.to_excel(f"output\{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx", index= False)
            
    
        return states, terminal, reward

    def set_DR(self, actions):
        #logging.info(f"Action set: {actions}")
        for index, machine in enumerate(self.parameters["MACHINES"]):
            
            rule = actions["DR_machines"][index]
            if rule != 14:
                self.statistics["operating_machines"] += 1
            machine.dispatching_rule = rule


    def actions(self):
        
        actions = {}
        
        actions.update({"DR_machines": {"type":'int',
                                        "shape": self.parameters['NUM_MACHINES'],
                                        "num_values": 15}})
        

        return actions
    


    '''
    Generate machines in the production system
    '''
        
    def generate_machines(self):
        
        
        id_machine = self.dataset_machines["id_machine"]
        corrective_time = self.dataset_machines["corrective_time"]
        preventive_time = self.dataset_machines["preventive_time"]
        usefull_time = self.dataset_machines["usefull_time"]
        
        

        for index, machine in enumerate(id_machine):
            
            self.list_machines.append(Machines(env = self.env,
                                                id_machine = machine,
                                                statistics = self.statistics,
                                                parameters = self.parameters,
                                                usefull_time = usefull_time[index],
                                                preventive_time = preventive_time[index],
                                                corrective_time = corrective_time[index],
                                                machine_env = simpy.PriorityResource(self.env)))
        
        self.parameters["MACHINES"] = self.list_machines