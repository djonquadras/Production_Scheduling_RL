import simpy

class Order():
    """
    An order specifices a production request.
    An order has a *id_material* and a sequence of *prod_steps* to fulfill.
    """

    def __init__(self, env,
                 id_material,
                 material_type,
                 processing_time,
                 machine,
                 priority,
                 due_date,
                 statistics, parameters,
                 maintenance_job_based = False):
        
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
        self.material_type = material_type
        self.due_date = due_date
        self.processing_time = processing_time
        
        ##
        # Seleção da máquina
        ##
        
        self.machine = machine
            
        self.priority = priority
        self.sop = 0
        self.eop = 0
        self.time_processing = processing_time
        self.finished = False
        self.env.process(self.order_processing()) # Process started at creation
        self.process_now = 0
        self.remaining_processing_time = processing_time
        
        ####
        # Parametros de manutenção
        ####
        
        # Job- Based
        self.maintenance_job_based = maintenance_job_based
        


    
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
                 "machine": self.machine,
                 "priority": self.priority,
                 "sop": self.set_sop,
                 "eop": self.eop,
                 "waiting_time": self.get_total_waiting_time(),
                 "delay_time": self.time_delayed()}
        return order


           
            
    '''
    Simula o sistema produtivo
    '''
    def order_processing(self):
        
        self.set_sop()
        
        machine = self.machine
        priority = self.priority

        # If the optimization is rule-free
        if self.parameters["DISPATCHING_TYPE"] == "rule-based":

            min_queue_size = 0
                
            for position, mach in enumerate(self.parameters["MACHINES"]):
                
                if position == 0:
                    min_queue_size = len(mach.machine_env.queue)
                    machine = mach

                else:
                    if len(mach.machine_env.queue) < min_queue_size:
                        min_queue_size = len(mach.machine_env.queue)
                        machine = mach
            priority = self.priority(machine.dispatching_rule, self.processing_time)
        else:
            machine = self.parameters["MACHINES"][machine]    

        # Requires the selected machine
        with machine.machine_env.request(priority = priority) as req:
            
            yield req
                        
            # Add to statistics
            machine.num_processed_orders += 1
            machine.production_sequence.append(self.id_material)
            machine.times.append(self.env.now)
            
                    
            # Setup if necessary
            if machine.prev_material_type != self.material_type:
                
                # Add to Statistics
                machine.production_sequence.append("Setup")
                machine.times.append(self.env.now)
                machine.num_setup += 1
                self.statistics["num_setups"] += 1
                
                # Setup
                yield self.env.timeout(machine.setup_time)
                
                # Update last product type
                machine.set_new_material_tipe(self.material_type)
            
            # Start Processing
            yield self.env.timeout(self.processing_time)
            
            # Increase machine degradation 
            machine.remaining_usefull_life -= self.processing_time

            # If machine is broken, start corrective maintenance
            if machine.remaining_usefull_life <= 0:
                self.env.process(machine.corr_maintenance())
                
            # Check if job has maintenance after processing when maintenance is job-based
            if self.parameters["MAINTENANCE_TYPE"] == "job-based":
                if self.maintenance_job_based: 
                    self.env.process(machine.jobs_prev_maintenance())

          
               
            # Statistics
            self.set_eop()
            #if self.due_date < self.env.now:
            #    self.statistics["delayed_orders"] += 1
                    
            self.finished = True
                        
            self.statistics['orders_done'].append(self.id_material)
        
        