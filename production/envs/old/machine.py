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
                 dispatching_rule = 0,
                 periodo_manutencao = 999999):
        self.dispatching_rule = dispatching_rule
        self.statistics = statistics
        self.parameters = parameters
        self.env = env
        self.id_maquina = id_maquina
        self.broken = False
        self.prev_material_type = None
        self.tempo_setup = 40
        self.tempo_vida = tempo_vida
        self.periodo_manutencao = periodo_manutencao
        self.tempo_preventiva = tempo_preventiva
        self.tempo_corretiva = tempo_corretiva
        self.env.process(self.prev_maintenance()) # Process started at creation
#        self.env.process(self.corr_maintenance()) # Process started at creation
#        self.env.process(self.jobs_prev_maintenance()) # Process started at creation
        self.remaining_usefull_life = tempo_vida
        self.tipo_manutencao = self.parameters['TIPO_MANUTENCAO']
        self.machine_env = machine_env
        self.ordem_producao = []
        self.horarios = []
        self.horario_ultima_preventiva = 0
        self.in_job_preventive = False
        self.qnt_preventivas = 0
        self.qnt_corretivas = 0
        self.qnt_setup = 0
        self.mttr = 0
        self.mttf = 0
        self.qnt_ordens_processadas = 0

    '''
    Calcula o Mean Time To Repair (MTTR)
    '''
    def calc_MTTR(self):
        qnt_reparos = self.qnt_preventivas + self.qnt_corretivas
        if qnt_reparos == 0:
            return 0
        tempo_total = self.parameters["MIN_SIMULATION"]
        mttr = tempo_total/qnt_reparos
        self.mttr = mttr
        return mttr
        
    '''
    Calcula o Mean Time To Failure (MTTF)
    '''
    def calc_MTTF(self):
        qnt_quebras = self.qnt_corretivas
        if qnt_quebras == 0:
            return 0
        tempo_total = self.parameters["MIN_SIMULATION"]
        mttf = tempo_total/qnt_quebras
        self.mttf = mttf
        return mttf
    
    '''
    Muda o tipo de material antigo para o tipo novo
    '''
    def set_new_material_tipe(self, new_type):
        self.prev_material_type = new_type

    '''
    Setup para produção de ordens diferentes
    '''
    def setup(self, new_type):
        
        # Caso o tipo da ordem anterior seja diferente do tipo atual
        if self.prev_material_type != new_type:
            
            # Adiciona as estatísticas de setup
            self.ordem_producao.append("Setup")
            self.horarios.append(self.env.now)
            self.qnt_setup += 1
            
            # Realiza o setup
            yield self.env.timeout(self.tempo_setup)
            
            # Atualiza o tipo de material anterior
            self.set_new_material_tipe(new_type)
    
    
    '''
    Código para Manutenção Preventiva
    '''        
    def prev_maintenance(self):
        
        # Ocorre continuamene
        while True:
            
            # Caso o tipo de manutenção se "job-based", será realizado outro tipo de manutenção    
            if self.tipo_manutencao == "job-based":
                break
            
            # Aguarda até o momento da próxima manutenção
            yield self.env.timeout(self.periodo_manutencao*24*60)
            
            # Requisita a máquina com uma prioridade que coloque na frente da fila
            with self.machine_env.request(priority = -9999998) as req:
                yield req
                
                # Salva as estatísticas da manutenção
                self.statistics["preventive_maintenance"] += 1
                self.qnt_preventivas += 1
                self.ordem_producao.append("Preventiva")
                self.horarios.append(self.env.now)
                
                # Realiza a manutenção
                yield self.env.timeout(self.tempo_preventiva)
                
                # Atualiza o tempo de vida restante
                self.remaining_usefull_life = self.tempo_vida
                
                # Determina o horário da última manutenção
                self.horario_ultima_preventiva = self.env.now


    '''
    Código para Manutenção Corretiva
    '''                 
    def corr_maintenance(self):
        
        # Atualiza a estatística de máquinas quebradas
        self.statistics["broken_machines"] += 1
        
        # Requisita a máquina com uma prioridade que coloque na frente da fila
        with self.machine_env.request(priority = -9999999) as req:
            yield req
            
            # Salva as estatísticas da manutenção
            self.ordem_producao.append("Corretiva")
            self.qnt_corretivas += 1 
            self.horarios.append(self.env.now)
            
            # Realiza a manutenção
            yield self.env.timeout(self.tempo_corretiva)
            
            # Atualiza o tempo de vida restante
            self.remaining_usefull_life = self.tempo_vida
            
            # Atualiza o estado da máquina
            self.broken = False
    

                    
    '''
    Código para Manutenção Preventiva Baseada em Jobs
    '''        
    def jobs_prev_maintenance(self):
        
            
        # Requisita a máquina com uma prioridade que coloque na frente da fila
        with self.machine_env.request(priority = -9999998) as req:
            yield req
            
            # Salva as estatísticas da manutenção
            self.statistics["preventive_maintenance"] += 1
            self.qnt_preventivas +=1 
            self.ordem_producao.append("Preventiva")
            self.horarios.append(self.env.now)
            
            # Realiza a manutenção
            yield self.env.timeout(self.tempo_preventiva)
            
            # Atualiza o tempo de vida restante
            self.remaining_usefull_life = self.tempo_vida
            
            # Determina o horário da última manutenção
            self.horario_ultima_preventiva = self.env.now
            
            # Tira do Status de Manutenção Preventiva
            self.in_job_preventive = False
