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
                 statistics, parameters):
        self.statistics = statistics
        self.parameters = parameters
        self.env = env
        self.id_material = id_material
        self.tipo_material = tipo_material
        self.tempo_processamento_m1 = tempo_processamento_m1
        self.tempo_processamento_m2 = tempo_processamento_m2
        self.tempo_processamento_m3 = tempo_processamento_m3
        self.maquina_step1 = maquina_step1
        self.maquina_step2 = maquina_step2
        self.maquina_step3 = maquina_step3
        self.prioridade_m1 = prioridade_m1
        self.prioridade_m2 = prioridade_m2
        self.prioridade_m3 = prioridade_m3
        self.sop = -1
        self.eop = -1
        self.time_processing = 0
        self.time_handling = 0
        self.actual_step = 0
        self.finished = False
        self.current_location = None
        self.order_log = [["action", "order_ID", "sim_time", "resource_ID"]]
        self.processed = self.env.event()
        self.reserved = False
        self.env.process(self.order_processing()) # Process started at creation



    # SOP = start of production
    def set_sop(self):  
        self.sop = self.env.now
        self.statistics['order_sop'][self.id_material] = self.sop

    # EOP = end of production
    def set_eop(self):  
        self.eop = self.env.now
        self.statistics['order_eop'][self.id_material] = self.eop
        self.statistics['order_leadtime'][self.id_material] = self.eop - self.sop


    def get_total_waiting_time(self):
        result = self.env.now - self.sop - self.time_processing - self.time_handling
        return result

    def order_processing(self):
        
        machines = [self.maquina_step1, self.maquina_step2, self.maquina_step3]
        priorities = [self.prioridade_m1, self.prioridade_m2, self.prioridade_m3]
        processing_time = [self.tempo_processamento_m1, self.tempo_processamento_m2, self.tempo_processamento_m3]
        i = 0   
        self.set_sop()
        print(f"Início do processamento da ordem {self.id_material}")
        while not self.finished:

            if self.finished:
                break
        
            with machines[i].machine_env.request(priority = priorities[i]) as req:
                yield req
                # Verifica Necessidade de setup
                machines[i].setup(self.tipo_material)
                yield self.env.timeout(processing_time[i])
                machines[i].remaining_usefull_life -= processing_time[i]
                if machines[i].remaining_usefull_life <= 0:
                    machines[i].broken = True
                if i == 2:
                    self.finished = True
                

        self.set_eop()
        print(f"Fim do processamento da ordem {self.id_material} - Lead Time: {self.eop - self.sop}")
        self.statistics['orders_done'].append(self)