import simpy

class Order():

    def __init__(self, env,
                 id_material,
                 material_type,
                 processing_time,
                 start_date,
                 parameters,
                 statistics,
                 due_date):
        
        self.statistics = statistics
        self.parameters = parameters
        self.env = env
        self.id_material = id_material
        self.material_type = material_type
        self.start_date = start_date
        self.due_date = due_date
        self.processing_time = processing_time
        self.sop = 0
        self.eop = 0
        self.finished = False
        self.remaining_processing_time = processing_time
        
        self.env.process(self.input())
             
    

    def input(self):

        yield self.env.timeout(self.start_date)
        
        self.statistics['products_arrivals'] += 1
        self.parameters["ORDERS"].append(self)

        