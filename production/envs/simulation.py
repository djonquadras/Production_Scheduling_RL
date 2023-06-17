import sys
from tensorforce.environments import Environment
import numpy as np
from production.envs.initialize_env import define_production_parameters
from production.envs.initialize_env import define_production_statistics

from production.envs.machine import Maquinas
from production.envs.weibull import weibull
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
        periodo_manutencao =[]
        
        if self.parameters["TIPO_MANUTENCAO"] == "periodic":
            periodo_manutencao = actions["periodo_manutencao"]
        else:
            periodo_manutencao = [0] *65
                       
            
            
        
        
        for index, maquina in enumerate(id_maquina):
            #print(f"Criando Máquina {maquina}")
            self.lista_maquinas.append(Maquinas(env = self.env,
                                                id_maquina = maquina,
                                                statistics = self.statistics,
                                                parameters = self.parameters,
                                                tempo_vida = weibull(2.5, 600),
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
    
    '''
    Cria as ordens de produção do sistema produtivo
    '''
    def criar_ordens(self, actions):
        
        # Seleciona os parâmetros do excel
        id_material = self.dataset_ordens["id_material"]
        tipo_material = self.dataset_ordens["tipo_material"]
        tempo_processamento_maquina1 = self.dataset_ordens["tempo_processamento_maquina1"]
        tempo_processamento_maquina2 = self.dataset_ordens["tempo_processamento_maquina2"]
        tempo_processamento_maquina3 = self.dataset_ordens["tempo_processamento_maquina3"]
        due_date = self.dataset_ordens["due_date"]
        
        # Seleciona os parâmetros das ações
        maquina_step1 = actions["selecao_maquinas1"]
        maquina_step2 = actions["selecao_maquinas2"]
        maquina_step3 = actions["selecao_maquinas3"]
        prioridade_m1 = actions["prioridade_M1"]
        prioridade_m2 = actions["prioridade_M2"]
        prioridade_m3 = actions["prioridade_M3"]
        
        # Cria as listas de preventivas, para caso de manutenção job-based
        lista_preventiva_job_stage1 = []
        lista_preventiva_job_stage2 = []
        lista_preventiva_job_stage3 = []
        
        # Caso seja job-based, alimenta as listas
        if self.parameters["TIPO_MANUTENCAO"] == "job-based":
            lista_preventiva_job_stage1 = actions["prev_maint_job_M1"]
            lista_preventiva_job_stage2 = actions["prev_maint_job_M2"]
            lista_preventiva_job_stage3 = actions["prev_maint_job_M3"]
        else:
            lista_preventiva_job_stage1 = [False] * self.parameters["qnt_orders"]
            lista_preventiva_job_stage2 = [False] * self.parameters["qnt_orders"]
            lista_preventiva_job_stage3 = [False] * self.parameters["qnt_orders"]
            
                    
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
                                           parameters= self.parameters,
                                           manutencao_job_M1 = lista_preventiva_job_stage1[index],
                                           manutencao_job_M2 = lista_preventiva_job_stage2[index],
                                           manutencao_job_M3 = lista_preventiva_job_stage3[index]))
            
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
        self.statistics["broken_machines_log"].append(self.statistics["broken_machines"])
        self.statistics["delayed_orders_log"].append(self.statistics["delayed_orders"])
        self.statistics["maquinas_ocupadas_log"].append(self.statistics["maquinas_ocupadas"])
        self.statistics["rewards_log"].append(self.statistics["reward"])
        self.statistics["preventive_maintenance_log"].append(self.statistics["preventive_maintenance"])
            
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
        
        print("Criando o ambiente")
        self.env = simpy.Environment()
        print("Criando as máquinas")
        self.criar_maquinas(actions)
        print("Criando as ordens")
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
        print(f"Log de Máquinas Quebradas = {self.statistics['broken_machines_log']}")
        print(f"Log Manutenções Preventivas: {self.statistics['preventive_maintenance_log']}")
        print(f"Log de Rewards = {self.statistics['rewards_log']}")
        
        print(f"states = {states}")
        
        
        self.env = 0
        return states, terminal, reward


    '''
    Função Obrigatória para o Reinforcement Learning.
    Com base nela o agente cria as ações do modelo.
    
    def actions(self):
        
        # Cria o dicionário das ações. FORMATO MANDATÓRIO 
        actions = {}
        actions.update({"selecao_maquinas1": {"type":'int',
											  "shape": self.parameters["qnt_orders"],
											  "num_values": self.parameters['NUM_MACHINES_1_STAGE']}})

		# Seleciona as máquinas do segundo estágio para cada ordem
        actions.update({"selecao_maquinas2": {"type":'int',
											  "shape": self.parameters["qnt_orders"],
											  "num_values": self.parameters['NUM_MACHINES_2_STAGE']}})

		# Seleciona as máquinas do terceiro estágio para cada ordem
        actions.update({"selecao_maquinas3": {"type":'int',
											  "shape": self.parameters["qnt_orders"],
											  "num_values": self.parameters['NUM_MACHINES_3_STAGE']}})
		
		# Seleciona as prioridades no primeiro estágio para cada ordem        
        actions.update({"prioridade_M1":   {"type":'float',
											"shape": self.parameters["qnt_orders"]}})

		# Seleciona as prioridades no segundo estágio para cada ordem
        actions.update({"prioridade_M2":   {"type":'float',
											"shape": self.parameters["qnt_orders"]}})

		# Seleciona as prioridades no terceiro estágio para cada ordem
        actions.update({"prioridade_M3":   {"type":'float',
											"shape": self.parameters["qnt_orders"]}})
	

	
        actions.update({"periodo_manutencao":   {"type":'int',
												"num_values": 30,
												"shape": self.parameters["qnt_machines"]}})

        return actions
    '''        

    '''
    Função Obrigatória para o Reinforcement Learning.
    Com base nela o agente cria as ações do modelo.
    '''
    def actions(self):
        
        # Cria o dicionário das ações. FORMATO MANDATÓRIO 
        actions = {}
        
        # Se o tipo de Dispatching for "rule-based"
        if self.parameters["TIPO_DISPATCHING"] == "rule-based":
        
            # Seleciona as regras de despacho para as máquinas do primeiro estágio
            actions.update({"DR_M1": {"type":'int',
                                      "shape": self.parameters['NUM_MACHINES_1_STAGE'],
                                      "num_values": self.parameters['NUM_DISPATCHING_RULES']}})

            # Seleciona as regras de despacho para as máquinas do segundo estágio
            actions.update({"DR_M2": {"type":'int',
                                      "shape": self.parameters['NUM_MACHINES_2_STAGE'],
                                      "num_values": self.parameters['NUM_DISPATCHING_RULES']}})
            
            # Seleciona as regras de despacho para as máquinas do terceiro estágio
            actions.update({"DR_M3": {"type":'int',
                                      "shape": self.parameters['NUM_MACHINES_3_STAGE'],
                                      "num_values": self.parameters['NUM_DISPATCHING_RULES']}})
            
            # Determina a quantidade de máquinas operando no primeiro estágio
            actions.update({"NUM_M1": {"type":'int',
                                      "shape": 1,
                                      "num_values": self.parameters['NUM_MACHINES_1_STAGE']}})
            
        
        # Se o tipo de Dispatching for "rule-free"
        else:
            
            # Seleciona as máquinas do primeiro estágio para cada ordem
            actions.update({"selecao_maquinas1": {"type":'int',
                                                  "shape": self.parameters["qnt_orders"],
                                                  "num_values": self.parameters['NUM_MACHINES_1_STAGE']}})

            # Seleciona as máquinas do segundo estágio para cada ordem
            actions.update({"selecao_maquinas2": {"type":'int',
                                                  "shape": self.parameters["qnt_orders"],
                                                  "num_values": self.parameters['NUM_MACHINES_2_STAGE']}})

            # Seleciona as máquinas do terceiro estágio para cada ordem
            actions.update({"selecao_maquinas3": {"type":'int',
                                                  "shape": self.parameters["qnt_orders"],
                                                  "num_values": self.parameters['NUM_MACHINES_3_STAGE']}})
            
            # Seleciona as prioridades no primeiro estágio para cada ordem        
            actions.update({"prioridade_M1":   {"type":'float',
                                                "shape": self.parameters["qnt_orders"]}})

            # Seleciona as prioridades no segundo estágio para cada ordem
            actions.update({"prioridade_M2":   {"type":'float',
                                                "shape": self.parameters["qnt_orders"]}})

            # Seleciona as prioridades no terceiro estágio para cada ordem
            actions.update({"prioridade_M3":   {"type":'float',
                                                "shape": self.parameters["qnt_orders"]}})
        
        # Se o Tipo de Manutenção for baseado em jobs
        if self.parameters["TIPO_MANUTENCAO"] == "job-based":
            
            # Determina se haverá manutenção após cada job no primeiro estágio
            actions.update({"prev_maint_job_M1": {"type":'bool',
                                                  "shape": self.parameters["qnt_orders"]}})

            # Determina se haverá manutenção após cada job no segundo estágio
            actions.update({"prev_maint_job_M2": {"type":'bool',
                                                  "shape": self.parameters["qnt_orders"]}})
            
            # Determina se haverá manutenção após cada job no terceiro estágio
            actions.update({"prev_maint_job_M3": {"type":'bool',
                                                  "shape": self.parameters["qnt_orders"]}})
        
        # Se a manutenção for periódica    
        else: 
        
            actions.update({"periodo_manutencao":   {"type":'int',
                                                    "num_values": 30,
                                                    "shape": self.parameters["qnt_machines"]}})

        return actions
    
