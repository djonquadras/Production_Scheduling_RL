import sys
from tensorforce.environments import Environment
import numpy as np
from production.envs.initialize_env import define_production_parameters
from production.envs.initialize_env import define_production_statistics
import logging
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
        self.in_reset = False
        self.lista_maquinas = []
        self.lista_ordens = []
        
        self.dataset_ordens = pd.read_excel('inputs/dataset_ordens.xlsx')
        self.dataset_maquinas = pd.read_excel('inputs/dataset_maquinas.xlsx')
        self.quebra_maquinas = []
        for i in self.dataset_maquinas["id_maquina"]:
            self.quebra_maquinas.append(weibull(10,144))
        
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
        tempo_corretiva = self.dataset_maquinas["tempo_corretiva"]
        tempo_preventiva = self.dataset_maquinas["tempo_preventiva"]
        
        
        dispatching_rule = []
        if self.parameters["TIPO_DISPATCHING"] == "rule-based":
            #print(f"Dispatching Rules: {actions['DR_Maquinas']}")
            dispatching_rule = actions["DR_Maquinas"]
        else:
            dispatching_rule = [0]*self.parameters['NUM_MACHINES']
        
        if self.parameters["TIPO_MANUTENCAO"] == "periodic":
            periodo_manutencao = actions["periodo_manutencao"]
        else:
            periodo_manutencao = [0]*self.parameters["NUM_MACHINES"]
        
        
        for index, maquina in enumerate(id_maquina):
            #print(f"Criando Máquina {maquina}")
            self.lista_maquinas.append(Maquinas(env = self.env,
                                                id_maquina = maquina,
                                                statistics = self.statistics,
                                                parameters = self.parameters,
                                                tempo_vida = self.quebra_maquinas[index],
                                                tempo_preventiva = tempo_preventiva[index],
                                                tempo_corretiva = tempo_corretiva[index],
                                                machine_env = simpy.PriorityResource(self.env),
                                                periodo_manutencao = int(periodo_manutencao[index]),
                                                dispatching_rule = dispatching_rule[index]))
        
        self.parameters["MACHINES"] = self.lista_maquinas
          
    '''
    Função que cria os estados a serem retornados ao agente
    '''
    def calcula_estados(self):
        
        preventivas = []
        corretivas = []
        setup = []
        mttr = []
        mttf = []
        ordens_maquina = []

        if self.in_reset:
            preventivas = [0]*self.parameters["NUM_MACHINES"]
            corretivas = [0]*self.parameters["NUM_MACHINES"]
            setup = [0]*self.parameters["NUM_MACHINES"]
            mttr = [0]*self.parameters["NUM_MACHINES"]
            mttf = [0]*self.parameters["NUM_MACHINES"]
            ordens_maquina = [0]*self.parameters["NUM_MACHINES"]
        
        else:
            for maq in self.lista_maquinas:
                preventivas.append(float(maq.qnt_preventivas))
                corretivas.append(float(maq.qnt_corretivas))
                setup.append(float(maq.qnt_setup))
                mttr.append(maq.calc_MTTR())
                mttf.append(maq.calc_MTTF())
                ordens_maquina.append(float(maq.qnt_ordens_processadas))
        
        
        # Quantidade de máquinas operando
        maquinas_operando = [float(self.statistics["maquinas_ocupadas"])]
        delayed_orders = [float(self.statistics["delayed_orders"])]
        
        states = np.concatenate([maquinas_operando,
                                 preventivas,
                                 corretivas,
                                 setup,
                                 ordens_maquina,
                                 mttf,
                                 mttr,
                                 delayed_orders])

        
        return states
    
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

        maquina_step1 = []
        maquina_step2 = []
        maquina_step3 = []
        prioridade_m1 = []
        prioridade_m2 = []
        prioridade_m3 = []
        maquinas_operando = 0
        
        if self.parameters["TIPO_DISPATCHING"] == "rule-free":
            prioridade_m1 = actions["prioridades"][:self.parameters["qnt_orders"]]
            prioridade_m2 = actions["prioridades"][self.parameters["qnt_orders"] : self.parameters["qnt_orders"]*2]
            prioridade_m3 = actions["prioridades"][self.parameters["qnt_orders"]*2 : self.parameters["qnt_orders"]*3]
            maquina_step1 = actions["selecao_maquinas1"]
            maquina_step2 = actions["selecao_maquinas2"]
            maquina_step3 = actions["selecao_maquinas3"]
            maquinas_operando = len(pd.DataFrame({"b": actions["selecao_maquinas1"]})["b"].unique())
        else:        
            maquinas_operando = actions["Operating_Machines"][0]
            maquina_step1 = [maquinas_operando]*self.parameters["qnt_orders"]
            maquina_step2 = [maquinas_operando]*self.parameters["qnt_orders"]
            maquina_step3 = [maquinas_operando]*self.parameters["qnt_orders"]

        
        
        # Cria as listas de preventivas, para caso de manutenção job-based
        lista_preventiva_job_stage1 = []
        lista_preventiva_job_stage2 = []
        lista_preventiva_job_stage3 = []
        
        # Caso seja job-based, alimenta as listas
        if self.parameters["TIPO_MANUTENCAO"] == "job-based":
            lista_preventiva_job_stage1 = actions["prev_maint_job"][:self.parameters["qnt_orders"]]
            lista_preventiva_job_stage2 = actions["prev_maint_job"][self.parameters["qnt_orders"] : self.parameters["qnt_orders"]*2]
            lista_preventiva_job_stage3 = actions["prev_maint_job"][self.parameters["qnt_orders"]*2 : self.parameters["qnt_orders"]*3]
        else:
            lista_preventiva_job_stage1 = [False] * self.parameters["qnt_orders"]
            lista_preventiva_job_stage2 = [False] * self.parameters["qnt_orders"]
            lista_preventiva_job_stage3 = [False] * self.parameters["qnt_orders"]
            
                    
        self.statistics["maquinas_ocupadas"] = maquinas_operando
        
        for index, ordem in enumerate(id_material):
            
            maquina_step1a = 0
            maquina_step2a = 0
            maquina_step3a = 0
            prioridade_m1a = 0
            prioridade_m2a = 0 
            prioridade_m3a = 0
            
            if self.parameters["TIPO_DISPATCHING"] == "rule-free":

                maquina_step1a = self.lista_maquinas[int(maquina_step1[index])]
                maquina_step2a = self.lista_maquinas[60 + int(maquina_step2[index])]
                maquina_step3a = self.lista_maquinas[62 + int(maquina_step3[index])]
                prioridade_m1a = float(prioridade_m1[index])
                prioridade_m2a = float(prioridade_m2[index])
                prioridade_m3a = float(prioridade_m3[index])

            else:        

                maquina_step1a = maquinas_operando
                maquina_step2a = maquinas_operando
                maquina_step3a = maquinas_operando        
                prioridade_m1a = maquinas_operando
                prioridade_m2a = maquinas_operando
                prioridade_m3a = maquinas_operando
            
            self.lista_ordens.append(Order(self.env,
                                           id_material = ordem,
                                           tipo_material = tipo_material[index],
                                           tempo_processamento_m1 = tempo_processamento_maquina1[index],
                                           tempo_processamento_m2 = tempo_processamento_maquina2[index],
                                           tempo_processamento_m3 = tempo_processamento_maquina3[index],
                                           maquina_step1 = maquina_step1a,
                                           maquina_step2 = maquina_step2a,
                                           maquina_step3 = maquina_step3a,
                                           prioridade_m1 = prioridade_m1a,
                                           prioridade_m2 = prioridade_m2a,
                                           prioridade_m3 = prioridade_m3a,
                                           due_date = due_date[index],
                                           statistics = self.statistics,
                                           parameters= self.parameters,
                                           manutencao_job_M1 = lista_preventiva_job_stage1[index],
                                           manutencao_job_M2 = lista_preventiva_job_stage2[index],
                                           manutencao_job_M3 = lista_preventiva_job_stage3[index]))
            
        
    def states(self):
        number = 0
        
        # Quantidade de máquinas operando
        number += 1
        
        # Quantidade de preventivas
        number += self.parameters["NUM_MACHINES"]
        
        # Quantidade de corretivas
        number += self.parameters["NUM_MACHINES"]
        
        # Quantidade de setups
        number += self.parameters["NUM_MACHINES"]
        
        # Quantidade de ordens alocadas por máquina
        number += self.parameters["NUM_MACHINES"]
        
        # MTTF por máquina
        number += self.parameters["NUM_MACHINES"]
        
        # MTTR por máquina
        number += self.parameters["NUM_MACHINES"]
        
        # Quantidade de ordens atrasadas
        number += 1

        
        return {"type":'float',
                "shape": number}
    
    # Optional additional steps to close environment
    def close(self):
        super().close()

    def reset(self):
        self.in_reset = True
        states = self.calcula_estados()
        self.in_reset = False
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
        reward += -3*self.statistics["broken_machines"]
        reward += -3*self.statistics["delayed_orders"]
        reward += -1*self.statistics["maquinas_ocupadas"]
        reward += -1*self.statistics["preventive_maintenance"]
        self.statistics["reward"] = reward
        return reward
    
    def execute(self, actions):

        print(f"<------------------------ Início da Execução {self.counter} ------------------------>")
        print(f"Reward Atual = {self.statistics['reward']}")
        print(f"Máquinas quebradas = {self.statistics['broken_machines']}")
        print(f" Ordens Atrasadas = {self.statistics['delayed_orders']}")
        print(f"Máquinas Ocupadas = {self.statistics['maquinas_ocupadas']}")
        print(f"Preventivas ocorridas = {self.statistics['preventive_maintenance']}")
        # Iniciando o setup
        reward = None
        terminal = False
        states = None
        self.counter += 1
        
        self.reset_states()
        
        #print("Criando o ambiente")
        self.env = simpy.Environment()
        #print("Criando as máquinas")
        self.criar_maquinas(actions)
        #print("Criando as ordens")
        self.criar_ordens(actions)
        
        #print("")
        #print("")
        
        #print("")
        #print("")

        
        
        
        self.env.run(until = self.parameters["MIN_SIMULATION"])


        reward = self.calcula_reward()
        self.update_historico()
        states = self.calcula_estados()

        
        if self.counter == self.parameters["episodes"]:
        #    print("Last episode action ", datetime.now())
            terminal = True
         
            for maquina in self.lista_maquinas:
                logging.info(f" Máquina {maquina.id_maquina} = {maquina.ordem_producao}")
                logging.info("")
            
            logging.info("")
            logging.info("")
            logging.info("Máquinas Quebradas")    
            logging.info(self.statistics["broken_machines_log"])
            logging.info("")
            logging.info("Ordens Atrasadas")    
            logging.info(self.statistics["delayed_orders_log"])
            logging.info("")
            logging.info("Máquinas Ocupadas")    
            logging.info(self.statistics["maquinas_ocupadas_log"])
            logging.info("")
            logging.info("Preventivas Realizadas")    
            logging.info(self.statistics["preventive_maintenance_log"])
            logging.info("")
            logging.info("Rewards")    
            logging.info(self.statistics["rewards_log"])
            

        #print("<------------------------ Fim da Execução ------------------------>")        
        
        

        #terminal = True  # Always False if no "natural" terminal state
            
        if terminal:    
            self.parameters.update({"ACTION": actions})
            

        #print(f"Log de Máquinas Quebradas = {self.statistics['broken_machines_log']}")
        #print(f"Log Manutenções Preventivas: {self.statistics['preventive_maintenance_log']}")
        #print(f"Log de Rewards = {self.statistics['rewards_log']}")
        
        #print(f"states = {states}")
        
        
        self.env = None
        self.lista_maquinas = None
        self.lista_ordens = None
        
        self.lista_maquinas = []
        self.lista_ordens = []
        
        return states, terminal, reward



    '''
    Função Obrigatória para o Reinforcement Learning.
    Com base nela o agente cria as ações do modelo.
    '''
    def actions(self):
        
        # Cria o dicionário das ações. FORMATO MANDATÓRIO 
        actions = {}
        
        # Se o tipo de Dispatching for "rule-based"
        if self.parameters["TIPO_DISPATCHING"] == "rule-based":
            
            # Seleciona as regras de despacho para as máquinas
            actions.update({"DR_Maquinas": {"type":'int',
                                            "shape": self.parameters['NUM_MACHINES'],
                                            "num_values": self.parameters['NUM_DISPATCHING_RULES']}})

            
            # Determina a quantidade de máquinas operando no primeiro estágio
            actions.update({"Operating_Machines": {"type":'int',
                                                   "shape": 1,
                                                   "num_values": self.parameters['NUM_MACHINES_1_STAGE']}})
            
        
        # Se o tipo de Dispatching for "rule-free"
        else:
            
            # Seleciona as máquinas para produção
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
            
            # Seleciona as prioridades em cada máquina        
            actions.update({"prioridades":  {"type":'float',
                                             "shape": self.parameters["qnt_orders"]*3}})

        
        # Se o Tipo de Manutenção for baseado em jobs
        if self.parameters["TIPO_MANUTENCAO"] == "job-based":
            
            # Determina se haverá manutenção após cada job
            actions.update({"prev_maint_job": {"type":'bool',
                                               "shape": self.parameters["qnt_orders"]*3}})
        
        # Se a manutenção for periódica    
        else: 
        
            actions.update({"periodo_manutencao":   {"type":'int',
                                                    "num_values": 30,
                                                    "shape": self.parameters["qnt_machines"]}})

        return actions
    
