#from production.envs.heuristics import *
import simpy
import numpy as np

class Maquinas():
    agent = None

    def __init__(self, env,
                 id_maquina,
                 statistics,
                 parameters,
                 tempo_vida,
                 tempo_preventiva,
                 tempo_corretiva,
                 machine_env,
                 periodo_manutencao = 999999):
        self.statistics = statistics
        self.parameters = parameters
        self.env = env
        self.id_maquina = id_maquina
        self.broken = False
        self.last_repair_time = 0.0
        self.type = "machine"
        self.time_broken_left = 0.0
        self.idle = env.event()
        self.last_broken_start = 0.0
        self.last_broken_time = 0.0
        self.last_process_start = 0.0
        self.last_process_start_stat = 0.0
        self.last_process_time = 0.0
        self.last_process_end = 0.0
        self.time_start_idle = 0.0
        self.time_start_idle_stat = 0.0
        self.counter = 0
        self.sum_reward = 0
        self.last_utilization_calc = 0.0
        self.prev_material_type = None
        self.tempo_setup = 40
        self.tempo_vida = tempo_vida
        self.periodo_manutencao = periodo_manutencao
        self.tempo_preventiva = tempo_preventiva
        self.tempo_corretiva = tempo_corretiva
        self.env.process(self.prev_maintenance()) # Process started at creation
        self.env.process(self.corr_maintenance()) # Process started at creation
        self.remaining_usefull_life = tempo_vida
        self.tipo_manutencao = self.parameters['TIPO_MANUTENCAO']
        self.machine_env = machine_env
        self.in_maintenance = False 

    def set_new_material_tipe(self, new_type):
        self.prev_material_tipe = new_type

    '''
    INCLUIR AQUI O REWARD DE SETUP
    '''
    def setup(self, new_type):
        if self.prev_material_type != new_type:
            yield self.env.timeout(self.tempo_setup)
            self.set_new_material_tipe(new_type)
            
    def prev_maintenance(self):
        while True:    
            if self.tipo_manutencao == "job-based":
                break
            yield self.env.timeout(self.periodo_manutencao*24*60)
            self.in_maintenance = True
            with self.machine_env.request(priority = -9999998) as req:
                yield req
                yield self.env.timeout(self.tempo_preventiva)
                self.in_maintenance = False
        
    def corr_maintenance(self):
        while True:
            yield self.env.timeout(abs(self.remaining_usefull_life))
            self.broken = True
            with self.machine_env.request(priority = -9999999) as req:
                yield req
                yield self.env.timeout(self.tempo_corretiva)
                self.broken = False
                    
