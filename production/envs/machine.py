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
                 machine_env,
                 dispatching_rule = 0,
                 maintenance_period = 999999):
        
        self.dispatching_rule = dispatching_rule
        self.statistics = statistics
        self.parameters = parameters
        self.env = env
        self.id_machine = id_machine
        self.broken = False
        self.prev_material_type = None
        self.setup_time = 0.75
        self.usefull_time = usefull_time
        self.maintenance_period = maintenance_period
        self.preventive_time = preventive_time
        self.corrective_time = corrective_time
        self.env.process(self.prev_maintenance()) # Process started at creation

        self.remaining_usefull_life = usefull_time
        self.maintenance_type = self.parameters['MAINTENANCE_TYPE']
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
    

    def set_new_material_tipe(self, new_type):
        self.prev_material_type = new_type


    
    
    '''
    Preventive Maintenance
    '''        
    def prev_maintenance(self):
        

        while True:
            
            # If maintenance type equals to "job-based", break
            if self.maintenance_type == "job-based":
                break
            
            # Wait for the maintenance time
            yield self.env.timeout(self.maintenance_period)
            
            # Request machine with high priority
            with self.machine_env.request(priority = -9999998) as req:
                yield req
                
                # Statistics
                self.statistics["preventive_maintenance"] += 1
                self.num_preventives += 1
                self.production_sequence.append("Preventive")
                self.times.append(self.env.now)
                
                # Maintin
                yield self.env.timeout(self.preventive_time)
                
                # Update remaining usefull time
                self.remaining_usefull_life = self.usefull_time
                
                # Update last maintenance time
                self.last_preventive_time = self.env.now


    '''
    Corrective Maintenance
    '''                 
    def corr_maintenance(self):
        
        # Statistics
        
        
        # Requests the machine with high pripority
        with self.machine_env.request(priority = -9999999) as req:
            yield req
            
            # Statistics 
            self.production_sequence.append("Corrective")
            self.num_correctives += 1 
            self.times.append(self.env.now)
            self.statistics["broken_machines"] += 1
            
            # Maintain
            yield self.env.timeout(self.corrective_time)
            
            # Update remaining usefull time 
            self.remaining_usefull_life = self.usefull_time
            
            # Update machine state
            self.broken = False
    

                    
    '''
    Job-Based Preventive Maintenance
    '''        
    def jobs_prev_maintenance(self):
        
            
        # Requests machine with high priority
        with self.machine_env.request(priority = -9999998) as req:
            yield req
            
            # Statistics
            self.statistics["preventive_maintenance"] += 1
            self.num_preventives +=1 
            self.production_sequence.append("Preventive")
            self.times.append(self.env.now)
            
            # Maintain
            yield self.env.timeout(self.preventive_time)
            
            # Update remaining usefull time
            self.remaining_usefull_life = self.usefull_time
            
            # Update last maintenance time
            self.last_preventive_time = self.env.now
            
            # Update machine state
            self.in_job_preventive = False
