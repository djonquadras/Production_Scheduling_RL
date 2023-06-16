import sys
from tensorforce.environments import Environment
import numpy as np
from production.envs.initialize_env import define_production_parameters
from production.envs.initialize_env import define_production_statistics
from production.envs.resources import *
from production.envs.machine import Maquinas
from production.envs.order import Order
from datetime import datetime
import simpy
import pandas as pd

'''
Função para simular o sistema produtivo
'''
class ProductionEnv(Environment):
    
    def __init__(self):
        
        super().__init__()
        self.count_episode = 0

        # Cria a variável que será o ambiente e seus parâmetros
        self.env = 0
        self.counter = 0 
        self.lista_maquinas = []
        self.lista_ordens = []
        
        self.dataset_ordens = pd.read_excel('inputs/dataset_ordens.xlsx')
        self.dataset_maquinas = pd.read_excel('inputs/dataset_maquinas.xlsx')
        
        # Define os parâmetros de toda a simulação
        self.parameters = define_production_parameters(episode = self.count_episode)
        self.parameters.update({'qnt_orders': self.dataset_ordens.shape[0]})
        self.parameters.update({'qnt_machines': self.dataset_maquinas.shape[0]})
        
        # Define as estatísticas de toda a simulação
        self.statistics, self.stat_episode = define_production_statistics(parameters=self.parameters)

    '''
    Função que cria as máquinas do sistema produtivo
    '''
        
    def criar_maquinas(self, actions):
        
        
        #INCLUIR lista_preventiva_job
        
        id_maquina = self.dataset_maquinas["id_maquina"]
        tempo_vida = self.dataset_maquinas["tempo_vida"]
        tempo_corretiva = self.dataset_maquinas["tempo_corretiva"]
        tempo_preventiva = self.dataset_maquinas["tempo_preventiva"]
        periodo_manutencao = actions["periodo_manutencao"]
        
        for index, maquina in enumerate(id_maquina):
            #print(f"Criando Máquina {maquina}")
            self.lista_maquinas.append(Maquinas(env = self.env,
                                                id_maquina = maquina,
                                                statistics = self.statistics,
                                                parameters = self.parameters,
                                                tempo_vida = tempo_vida[index],
                                                tempo_preventiva = tempo_preventiva[index],
                                                tempo_corretiva = tempo_corretiva[index],
                                                machine_env = simpy.PriorityResource(self.env),
                                                periodo_manutencao = int(periodo_manutencao[index])))
        
        #print("Todas as Máquinas Criadas!")
        #print("")
        #print("")
        #print("")    
    
    def calcula_estados(self):
        return[float(self.statistics["broken_machines"]),
               float(self.statistics["delayed_orders"]),
               float(self.statistics["maquinas_ocupadas"])]
    
    def criar_ordens(self, actions):
        id_material = self.dataset_ordens["id_material"]
        tipo_material = self.dataset_ordens["tipo_material"]
        tempo_processamento_maquina1 = self.dataset_ordens["tempo_processamento_maquina1"]
        tempo_processamento_maquina2 = self.dataset_ordens["tempo_processamento_maquina2"]
        tempo_processamento_maquina3 = self.dataset_ordens["tempo_processamento_maquina3"]
        due_date = self.dataset_ordens["due_date"]
        maquina_step1 = actions["selecao_maquinas1"]
        maquina_step2 = actions["selecao_maquinas2"]
        maquina_step3 = actions["selecao_maquinas3"]
        prioridade_m1 = actions["prioridade_M1"]
        prioridade_m2 = actions["prioridade_M2"]
        prioridade_m3 = actions["prioridade_M3"]
        
        self.statistics["maquinas_ocupadas"] = len(pd.DataFrame({"b": actions["selecao_maquinas1"]})["b"].unique())
        
        for index, ordem in enumerate(id_material):
            #print(f"Criando Ordem {ordem}")
            self.lista_ordens.append(Order(self.env,
                                           id_material = ordem,
                                           tipo_material = tipo_material[index],
                                           tempo_processamento_m1 = tempo_processamento_maquina1[index],
                                           tempo_processamento_m2 = tempo_processamento_maquina2[index],
                                           tempo_processamento_m3 = tempo_processamento_maquina3[index],
                                           maquina_step1 = self.lista_maquinas[int(maquina_step1[index])],
                                           maquina_step2 = self.lista_maquinas[60 + int(maquina_step2[index])],
                                           maquina_step3 = self.lista_maquinas[62 + int(maquina_step3[index])],
                                           prioridade_m1 = float(prioridade_m1[index]),
                                           prioridade_m2 = float(prioridade_m2[index]),
                                           prioridade_m3 = float(prioridade_m3[index]),
                                           due_date = due_date[index],
                                           statistics = self.statistics,
                                           parameters= self.parameters))
            
        #print("Todas as Ordens Criadas!")
        #print("")
        #print("")
        #print("")
        
    def states(self):
        return {"type":'float',
                "shape": 3}
    
    # Optional additional steps to close environment
    def close(self):
        super().close()

    def reset(self):
        states = self.calcula_estados()
        return states
    
    def reset_states(self):
        self.statistics["broken_machines"] = 0
        self.statistics["delayed_orders"] = 0
        self.statistics["maquinas_ocupadas"] = 0
        self.statistics["reward"] = 0
        self.statistics["preventive_maintenance"] = 0
        
    def update_historico(self):
        self.statistics["hist_broken_machines"].append(self.statistics["broken_machines"])
        self.statistics["hist_delayed_orders"].append(self.statistics["delayed_orders"])
        self.statistics["hist_maquinas_ocupadas"].append(self.statistics["maquinas_ocupadas"])
        self.statistics["hist_rewards"].append(self.statistics["reward"])
            
    def calcula_reward(self):
        reward = 0
        reward = -2*self.statistics["broken_machines"]
        reward = -2*self.statistics["delayed_orders"]
        reward = -1*self.statistics["maquinas_ocupadas"]
        reward = -1*self.statistics["preventive_maintenance"]
        self.statistics["reward"] = reward
        return reward
    
    def execute(self, actions):

        # Iniciando o setup
        reward = None
        terminal = False
        states = None
        self.counter += 1
        
        self.reset_states()
        
        self.env = simpy.Environment()
        self.criar_maquinas(actions)
        self.criar_ordens(actions)
        
        print("")
        print("")
        print(f"<------------------------ Início da Execução {self.counter} ------------------------>")
        print("")
        print("")

        
        
        
        self.env.run(until = 10200)
        
        for maquina in self.lista_maquinas:
            print(f" Máquina {maquina.id_maquina} = {maquina.ordem_producao}")
            print("")
            print("")
        print("<------------------------ Fim da Execução ------------------------>")        
        
        

        terminal = True  # Always False if no "natural" terminal state
            
        if terminal:    
            self.parameters.update({"ACTION": actions})
            
        reward = self.calcula_reward()
        self.update_historico()
        states = self.calcula_estados()
        print(f"Histórico de Máquinas Quebradas = {self.statistics['hist_broken_machines']}")
        print(f"Histórico de Rewards = {self.statistics['hist_rewards']}")
        
        print(f"states = {states}")
        
        
        self.env = 0
        return states, terminal, reward
        


    def actions(self):
        actions = {}
        
        actions.update({"selecao_maquinas1": {"type":'int',
                                              "shape": self.parameters["qnt_orders"],
                                              "num_values": 60}})
        actions.update({"selecao_maquinas2": {"type":'int',
                                              "shape": self.parameters["qnt_orders"],
                                              "num_values": 2}})
        actions.update({"selecao_maquinas3": {"type":'int',
                                              "shape": self.parameters["qnt_orders"],
                                              "num_values": 3}})
        
        
        actions.update({"prioridade_M1":   {"type":'float',
                                         "shape": self.parameters["qnt_orders"]}})
        actions.update({"prioridade_M2":   {"type":'float',
                                         "shape": self.parameters["qnt_orders"]}})
        actions.update({"prioridade_M3":   {"type":'float',
                                         "shape": self.parameters["qnt_orders"]}})
        
        
        actions.update({"periodo_manutencao":   {"type":'int',
                                                 "num_values": 30,
                                                 "shape": self.parameters["qnt_machines"]}})

        return actions
    
        # Se for Rule-Free
        if self.parameters['TIPO_DISPATCHING'] == 'rule-free':
            
            # Seleção da Máquina do Primeiro Estágio      
            actions.update({"selecao_maquinas1": {"type":'int',
                                                  "shape": self.parameters["qnt_orders"],
                                                  "num_values": 60}})
            
            # Prioridades das Ordens
            actions.update({"prioridade":   {"type":'float',
                                             "shape": self.parameters["qnt_orders"]}})
        
        # Se for Rule-Based 
        else:
            # Seleciona a Ordem de Despacho para cada máquina
            actions.update({"dispatching_rule": {"type":'int',
                                                 "num_values": 4,
                                                 "shape": self.parameters["qnt_machines"]}})
            
            # Seleciona a Quantidade de Máquinas funcionando No Estágio 1
            actions.update({"qnt_machines": {"type":'int',
                                             "num_values": 60,
                                             "shape": self.parameters["qnt_machines"]}})
        
        # Se a manutenção for baseada em jobs
        if self.parameters['TIPO_MANUTENCAO'] == 'job-based':
            # Determina se a manutenção preventiva deve ocorrer após o job
            actions.update({"manutencao_job":   {"type":'bool',
                                                 "shape": self.parameters["qnt_orders"]}})
        
        # Se a manutenção for periódica
        else:
            # Determina a periodicidade de manutenção em cada máquina
            actions.update({"periodo_manutencao":   {"type":'int',
                                                     "num_values": 64800,
                                                     "shape": self.parameters["qnt_machines"]}})
        print("Action space created!")       
        return actions
        
        
    



