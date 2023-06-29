#from production.envs.heuristics import *
import simpy
import numpy as np

class Machines():
    agent = None

    def __init__(self, env,
                 id_machine,
                 statistics,
                 parameters,
                 usefull_time,
                 preventive_time,
                 corrective_time,
                 machine_env):
        
        self.dispatching_rule = 0
        self.statistics = statistics
        self.parameters = parameters
        self.env = env
        self.id_machine = id_machine
        self.broken = False
        self.prev_material_type = None
        self.setup_time = 0.75
        self.usefull_time = usefull_time
        self.preventive_time = preventive_time
        self.corrective_time = corrective_time
        self.env.process(self.execute())


        self.remaining_usefull_life = usefull_time

        self.machine_env = machine_env
        self.production_sequence = []
        self.times = []
        self.last_preventive_time = 0
        self.in_job_preventive = False
        self.num_preventives = 0
        self.num_correctives = 0
        self.num_setup = 0
        self.mttr = 0
        self.mttf = 0
        self.num_processed_orders = 0
        self.turned_off = False

    '''
    Mean Time To Repair (MTTR)
    '''
    def calc_MTTR(self):
        
        num_maintenance = self.num_preventives + self.num_correctives
        
        if num_maintenance == 0:
        
            self.statistics["mttr_log"][self.id_machine].append(0)
            return 0
        
        total_time = self.parameters["MIN_SIMULATION"]
        mttr = total_time/num_maintenance
        self.mttr = mttr
        self.statistics["mttr_log"][self.id_machine].append(mttr)
        return mttr
        
    '''
    Mean Time To Failure (MTTF)
    '''
    def calc_MTTF(self):
        num_breaks = self.num_correctives
        
        if num_breaks == 0:
            self.statistics["mttf_log"][self.id_machine].append(0)
            return 0
        total_time = self.parameters["MIN_SIMULATION"]
        mttf = total_time/num_breaks
        self.mttf = mttf
        self.statistics["mttf_log"][self.id_machine].append(mttf)
        return mttf

    
    '''
    Generate the remaining usefull life for each machine
    '''
    def calc_Remaining_Useful_Life(self):
        life = self.remaining_usefull_life
        
        if life == 0:
            self.statistics["remaining_usefull_life"][self.id_machine].append(0)
            return 0
        self.statistics["remaining_usefull_life"][self.id_machine].append(life)
        return life

    def sef_setup_time(self, new_type):
        if self.prev_material_type == new_type:
            return 0
        else:
            return self.setup_time    

    '''
    Function that return the order priorities for each machine considering Dispatching Rules
    '''
    def set_priority(self, job):
        
        # Shortest Processing Time (SPT)
        
        if self.dispatching_rule == 1:
            return job.processing_time
        
        # Longest Processing Time (LPT)
        elif self.dispatching_rule == 2:
            return (job.processing_time + self.sef_setup_time(job.material_type))*(-1)
        
        # Least Work Remaining (LWR)
        elif self.dispatching_rule == 3:
            return (job.remaining_processing_time + self.sef_setup_time(job.material_type))
        
        # Most Work Remaining (MWR)
        elif self.dispatching_rule == 4:
            return job.remaining_processing_time *(-1)
        
        # Earliest Due Date (EDD)
        elif self.dispatching_rule == 5:
            return job.due_date
        
        # First in First Out (FIFO)
        else:
            return 1
        


    def select_order_dispatching_rule(self):
        job = 0
        last_index = 0
        last_priority = 0
        
        for index, order in enumerate(self.parameters["ORDERS"]):
            
            job_priority = self.set_priority(order)
            
            if index == 0:
                last_priority = job_priority
                last_index = index
            
            if job_priority < last_priority:
                last_priority = job_priority
                last_index = index
        
        job = self.parameters["ORDERS"].pop(last_index)
        return job

    def execute(self):
        
        while True:
            
            if self.dispatching_rule == 14:
                self.turned_off = True
                break
            
            if self.dispatching_rule > 6:
                
                with self.machine_env.request(priority = -1) as req:
                    yield req
                    
                    self.statistics["preventive_maintenance"] += 1
                    self.num_preventives += 1
                    self.production_sequence.append("Preventive")
                    self.times.append(self.env.now)
                    
                    # Maintain
                    yield self.env.timeout(self.preventive_time)
                    
                    # Update remaining usefull time
                    self.remaining_usefull_life = self.usefull_time
                    
                    # Update last maintenance time
                    self.last_preventive_time = self.env.now
                    
                    self.dispatching_rule = self.dispatching_rule - 7

            if len(self.parameters["ORDERS"]) == 0:
                while len(self.parameters["ORDERS"]) == 0:
                    yield self.env.timeout(0.5)
            
            job = self.select_order_dispatching_rule()
            

            #print(f"Produzindo job {job.id_material}!")
            #print(f"{self.id_machine} - Começando a produzir o produto {job.id_material} no momento {self.env.now}")
            #print(f"{self.id_machine} - Tempo de produção do produto {job.id_material} = {job.processing_time}")
            with self.machine_env.request(priority = 1) as req:
                
                yield req
                            
                # Setup if necessary
                if self.prev_material_type != job.material_type:
                    
                    # Add to Statistics
                    self.production_sequence.append("Setup")
                    
                    self.times.append(self.env.now)
                    
                    self.num_setup += 1
                    
                    self.statistics["num_setups"] += 1
                    
                    
                    # Setup
                    yield self.env.timeout(self.setup_time)
                    #print(f"{self.id_machine} - Tempo de Setup = {self.setup_time}")
                    
                    # Update last product type
                    self.prev_material_type = job.material_type
                    
                # Add to statistics
                self.num_processed_orders += 1
                self.production_sequence.append(job.id_material)
                self.times.append(self.env.now)
                
                # Start Processing
                yield self.env.timeout(job.processing_time)
                #print(f"{self.id_machine} - Finalizando a produção do produto {job.id_material} no momento {self.env.now}")
                
                # Increase machine degradation 
                self.remaining_usefull_life -= job.processing_time

                # If machine is broken, start corrective maintenance
                if self.remaining_usefull_life <= 0:
                
                    # Statistics 
                    self.production_sequence.append("Corrective")
                    self.num_correctives += 1 
                    self.times.append(self.env.now)
                    self.statistics["broken_machines"] += 1
                    
                    # Maintain
                    yield self.env.timeout(self.corrective_time)
                    
                    # Update remaining usefull time 
                    self.remaining_usefull_life = self.usefull_time
                    
                
                self.statistics["daily_production"] +=1                                        
                job.finished = True
                

            #print(f"Finalizando job {job.id_material}!")
                            