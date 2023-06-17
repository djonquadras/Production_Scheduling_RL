import simpy

class Order():
    """
    An order specifices a production request.
    An order has a *id_material* and a sequence of *prod_steps* to fulfill.
    """

    def __init__(self, env,
                 id_material,
                 tipo_material,
                 tempo_processamento_m1,
                 tempo_processamento_m2,
                 tempo_processamento_m3,
                 maquina_step1,
                 maquina_step2,
                 maquina_step3,
                 prioridade_m1,
                 prioridade_m2,
                 prioridade_m3,
                 due_date,
                 statistics, parameters,
                 manutencao_job_M1 = False,
                 manutencao_job_M2 = False,
                 manutencao_job_M3 = False):
        
        ####
        # Parâmetros Gerais
        ####
        self.statistics = statistics
        self.parameters = parameters
        self.env = env
        
        ####
        # Parâmetros das Ordens de Produção
        ####
        self.id_material = id_material
        self.tipo_material = tipo_material
        self.due_date = due_date
        self.tempo_processamento_m1 = tempo_processamento_m1
        self.tempo_processamento_m2 = tempo_processamento_m2
        self.tempo_processamento_m3 = tempo_processamento_m3
        
        ##
        # Seleção da máquina
        ##
        
        self.maquina_step1 = maquina_step1
        self.maquina_step2 = maquina_step2
        self.maquina_step3 = maquina_step3
            
        self.prioridade_m1 = prioridade_m1
        self.prioridade_m2 = prioridade_m2
        self.prioridade_m3 = prioridade_m3
        self.sop = 0
        self.eop = 0
        self.time_processing = tempo_processamento_m1 + tempo_processamento_m2 + tempo_processamento_m3
        self.finished = False
        self.env.process(self.order_processing()) # Process started at creation
        self.process_now = 0
        self.remaining_processing_time = tempo_processamento_m1 + tempo_processamento_m2 + tempo_processamento_m3
        
        ####
        # Parametros de manutenção
        ####
        
        # Job- Based
        self.manutencao_job_M1 = manutencao_job_M1
        self.manutencao_job_M2 = manutencao_job_M2
        self.manutencao_job_M3 = manutencao_job_M3
        


    
    '''
    Function that return the order priorities for each machine considering Dispatching Rules
    '''
    def priority(self, rule, processing_time):
        
        # Shortest Processing Time (SPT)
        
        if rule == 1:
            return processing_time
        
        # Longest Processing Time (LPT)
        elif rule == 2:
            return processing_time*(-1)
        
        # Least Work Remaining (LWR)
        elif rule == 3:
            return self.remaining_processing_time
        
        # Most Work Remaining (MWR)
        elif rule == 4:
            return self.remaining_processing_time *(-1)
        
        # Earliest Due Date (EDD)
        elif rule == 5:
            return self.due_date
        
        # First in First Out (FIFO)
        else:
            return 1
        
    
    '''
    SOP = start of production
    '''
    def set_sop(self):  
        self.sop = self.env.now

    
    '''
    EOP = end of production
    '''
    def set_eop(self):  
        self.eop = self.env.now

    
    '''
    The total waiting time in the system
    '''
    def get_total_waiting_time(self):
        result = self.eop - (self.sop + self.time_processing)
        return result
    
    '''
    Check if the order is delayed
    '''
    def order_delayed(self):
        if self.due_date < self.env.now:
            return True
        else:
            return False
    
    '''
    Return the total delay time
    '''
    def time_delayed(self):
         if self.order_delayed():
             return self.eop - self.due_date
         else:
             return 0

    '''
    Return order log
    '''
    def return_log(self):
        order = {"order_id": self.id_material,
                 "machines_sequence": [self.maquina_step1, self.maquina_step2, self.maquina_step3],
                 "priorities": [self.prioridade_m1, self.prioridade_m2, self.prioridade_m3],
                 "sop": self.set_sop,
                 "eop": self.eop,
                 "waiting_time": self.get_total_waiting_time(),
                 "delay_time": self.time_delayed()}
        return order

    '''
    Simula o sistema produtivo
    '''
    def order_processing(self):
        
        print(f"Iniciando processamento da ordem {self.id_material} no minuto {self.env.now}")
        #Setup Parameters for simulation
        machines = []
        # Caso a produção seja "Rule-Free"
        if self.parameters["TIPO_DISPATCHING"] == "rule-free":
            machines = [self.maquina_step1, self.maquina_step2, self.maquina_step3]

        else:
            machines = [0,0,0]
        
        processing_time = [self.tempo_processamento_m1, self.tempo_processamento_m2, self.tempo_processamento_m3]        
        priorities = [self.prioridade_m1, self.prioridade_m2, self.prioridade_m3]

          
        
        manutencao_jobs = [self.manutencao_job_M1, self.manutencao_job_M2, self.manutencao_job_M3]
        self.set_sop()
        
        lista_maquinas_dr = []
        if self.parameters["TIPO_DISPATCHING"] == "rule-based":
            NUM_1 = self.parameters["NUM_MACHINES_1_STAGE"]
            NUM_2 = self.parameters["NUM_MACHINES_1_STAGE"] + self.parameters["NUM_MACHINES_2_STAGE"]
            NUM_3 = self.parameters["NUM_MACHINES_1_STAGE"] + self.parameters["NUM_MACHINES_2_STAGE"] + self.parameters["NUM_MACHINES_3_STAGE"]
            
            machines_1 = self.parameters["MACHINES"][:self.prioridade_m1]
            machines_2 = self.parameters["MACHINES"][NUM_1:NUM_2]
            machines_3 = self.parameters["MACHINES"][NUM_2:NUM_3]
            lista_maquinas_dr = [machines_1, machines_2, machines_3]
        
        
        
        while not self.finished:
            
            # Seleciona a máquina com menor fila para caso seja Rule-Based
            if self.parameters["TIPO_DISPATCHING"] == "rule-based":
                tam_fila_anterior = 0
                
                for posicao, machine in enumerate(lista_maquinas_dr[self.process_now]):
                    if posicao == 0:
                        tam_fila_anterior = len(machine.machine_env.queue)
                        machines[self.process_now] = machine
                    else:
                        if len(machine.machine_env.queue) < tam_fila_anterior:
                            tam_fila_anterior = len(machine.machine_env.queue)
                            machines[self.process_now] = machine
                
                priorities[self.process_now] = self.priority(machines[self.process_now].dispatching_rule, processing_time[self.process_now])
                

            if self.finished:
                break            

            
            # Requisita a máquina com a prioridade determinada
            #print(f"Tamanho da fila na máquina {machines[self.process_now].id_maquina}: {len(machines[self.process_now].machine_env.queue)}")        
            with machines[self.process_now].machine_env.request(priority = priorities[self.process_now]) as req:
                yield req
                print(f"Ordem {self.id_material} na máquina {machines[self.process_now].id_maquina}")
                
                #print(f"Produzindo a ordem {self.id_material} na máquina {machines[self.process_now].id_maquina}")
                
                # Adiciona a ordem nas estatísticas da máquina
                machines[self.process_now].ordem_producao.append(self.id_material)
                machines[self.process_now].horarios.append(self.env.now)
                
                # Verifica Necessidade de setup
                machines[self.process_now].setup(self.tipo_material)
                
                # Começa a produção da ordem
                yield self.env.timeout(processing_time[self.process_now])
                
                # Diminui a vida útil da máquina
                machines[self.process_now].remaining_usefull_life -= processing_time[self.process_now]

                # Se o tempo útil da máquina acabar, indicar que está quebrada
                if machines[self.process_now].remaining_usefull_life <= 0:
                    machines[self.process_now].broken = True
                    
                # Verifica se a máquina terá manutenção após o job
                if self.parameters["TIPO_MANUTENCAO"] == "job-based":
                    if manutencao_jobs[self.process_now]: 
                        machines[self.process_now].in_job_preventive = True

                # Diminui o remaining processing time
                self.remaining_processing_time -= processing_time[self.process_now]
                
                # Confere se é a última pare do processo
                if self.process_now == 2:
                    
                    # Adiciona as estatísticas
                    self.set_eop()
                    if self.due_date < self.env.now:
                        self.statistics["delayed_orders"] += 1
                        
                    # Indica que a ordem foi finalizada
                    self.finished = True
                    break
                
                # Se não for a última etapa, avança para a próxima
                self.process_now = self.process_now + 1
                
        print(f"Sequencia para {self.id_material}: [{machines[0].id_maquina}, {machines[1].id_maquina}, {machines[2].id_maquina}] - Prioridades: [{round(priorities[0], 3)}, {round(priorities[1],3)}, {round(priorities[2],3)}]")
        # Retorna as estatística na etapa final
        if self.parameters["TERMINAL"]:
            self.statistics['orders_done'].append(self.return_log(self))
        
        