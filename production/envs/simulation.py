import sys
from tensorforce.environments import Environment
import numpy as np
from production.envs.initialize_env import *
from production.envs.resources import *
from production.envs.machine import Maquinas
from production.envs.order import Order
from datetime import datetime
import simpy


# Função para simular o sistema produtivo
class ProductionEnv(Environment):
    
    def __init__(self):
        
        super().__init__()
        
        self.count_episode = 0
        self.last_export_time = 0.0
        self.last_export_real_time = datetime.now()

        # Simpy Environment + Tensorforce-Agent
        self.env = simpy.Environment()
        self.counter = 0
        self.agents = dict() 

        self.dataset_ordens = pd.read_excel('inputs/dataset_ordens.xlsx')
        self.dataset_maquinas = pd.read_excel('inputs/dataset_maquinas.xlsx')
        
        self.parameters = define_production_parameters(env=self.env, episode = self.count_episode)
        
        self.parameters.update({'qnt_orders': self.dataset_ordens.shape[0]})
        self.parameters.update({'qnt_machines': self.dataset_maquinas.shape[0]})
        

        self.statistics, self.stat_episode = define_production_statistics(parameters=self.parameters)
        self.lista_maquinas = []
        self.lista_ordens = []

        self.statistics['sim_start_time'] = datetime.now()
        
    def criar_maquinas(self, actions):
        id_maquina = self.dataset_maquinas["id_maquina"]
        tempo_vida = self.dataset_maquinas["tempo_vida"]
        tempo_corretiva = self.dataset_maquinas["tempo_corretiva"]
        tempo_preventiva = self.dataset_maquinas["tempo_preventiva"]
        periodo_manutencao = actions["periodo_manutencao"]
        
        for index, maquina in enumerate(id_maquina):
            print(f"Criando Máquina {maquina}")
            self.lista_maquinas.append(Maquinas(env = self.env,
                                                id_maquina = maquina,
                                                statistics = self.statistics,
                                                parameters = self.parameters,
                                                tempo_vida = tempo_vida[index],
                                                tempo_preventiva = tempo_preventiva[index],
                                                tempo_corretiva = tempo_corretiva[index],
                                                machine_env = simpy.PriorityResource(self.env),
                                                periodo_manutencao = int(periodo_manutencao[index])))
        print("Todas as Máquinas Criadas!")
        print("")
        print("")
        print("")    
    
    def criar_ordens(self, actions):
        id_material = self.dataset_ordens["id_material"]
        tipo_material = self.dataset_ordens["tipo_material"]
        tempo_processamento_maquina1 = self.dataset_ordens["tempo_processamento_maquina1"]
        tempo_processamento_maquina2 = self.dataset_ordens["tempo_processamento_maquina2"]
        tempo_processamento_maquina3 = self.dataset_ordens["tempo_processamento_maquina3"]
        maquina_step1 = actions["selecao_maquinas1"]
        maquina_step2 = actions["selecao_maquinas2"]
        maquina_step3 = actions["selecao_maquinas3"]
        prioridade_m1 = actions["prioridade_M1"]
        prioridade_m2 = actions["prioridade_M2"]
        prioridade_m3 = actions["prioridade_M3"]
        
        for index, ordem in enumerate(id_material):
            print(f"Criando Ordem {ordem}")
            self.lista_ordens.append(Order(self.env,
                                           id_material = ordem,
                                           tipo_material = tipo_material[index],
                                           tempo_processamento_m1 = tempo_processamento_maquina1[index],
                                           tempo_processamento_m2 = tempo_processamento_maquina2[index],
                                           tempo_processamento_m3 = tempo_processamento_maquina3[index],
                                           maquina_step1 = self.lista_maquinas[int(maquina_step1[index])],
                                           maquina_step2 = self.lista_maquinas[int(maquina_step2[index])],
                                           maquina_step3 = self.lista_maquinas[int(maquina_step3[index])],
                                           prioridade_m1 = float(prioridade_m1[index]),
                                           prioridade_m2 = float(prioridade_m2[index]),
                                           prioridade_m3 = float(prioridade_m3[index]),
                                           statistics = self.statistics,
                                           parameters= self.parameters))
            
        print("Todas as Ordens Criadas!")
        print("")
        print("")
        print("")
        



    def states(self):
        return {"type":'float',
                "shape": (8,)}
    
    # Optional additional steps to close environment
    def close(self):
        super().close()

    def reset(self):
        state = np.random.random(size=(8,))
        return state
            
    
    
    def execute(self, actions):
        print("")
        print("")
        print("")
        print("")
        print("<------------------------ Início da Execução ------------------------>")
        print("")
        print("")
        print("")
        print("")
        self.criar_maquinas(actions)
        self.criar_ordens(actions)
        self.env.run(until = 43200)
        print("<------------------------ Início da Execução ------------------------>")        
        
        next_state = np.random.random(size=(8,))
        terminal = True  # Always False if no "natural" terminal state
            
        if terminal:    
            self.parameters.update({"ACTION": actions})

        
        reward = np.random.random()
        return next_state, terminal, reward
        


    def actions(self):
        actions = {}
        
        actions.update({"selecao_maquinas1": {"type":'int',
                                              "shape": self.parameters["qnt_orders"],
                                              "num_values": 60}})
        actions.update({"selecao_maquinas2": {"type":'int',
                                              "shape": self.parameters["qnt_orders"],
                                              "num_values": 60}})
        actions.update({"selecao_maquinas3": {"type":'int',
                                              "shape": self.parameters["qnt_orders"],
                                              "num_values": 60}})
        
        
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
        
        
    



