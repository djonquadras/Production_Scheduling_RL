from resources import *
from production.envs.time_calc import *
from production.envs.heuristics import *



class Order(Resource):

    """
    An order specifices a production request.
    """

    def __init__(self,
                 env,
                 id,
                 variant,
                 statistics,
                 parameters,
                 resources,
                 agents,
                 time_calc):
        
        Resource.__init__(self,
                          statistics,
                          parameters,
                          resources,
                          agents,
                          time_calc,
                          None)
        
        self.env = env
        self.id = id
        self.variant = variant
        self.sop = -1
        self.eop = -1
        self.time_processing = 0
        self.time_handling = 0
        self.actual_step = 0
        self.finished = False
        self.order_log = [["action", "order_ID", "sim_time", "resource_ID"]]
        self.processed = self.env.event()
        self.reserved = False
        if self.parameters['PRINT_CONSOLE']: print("Order %s created %s" % (self.id, [x.id for x in self.prod_steps]))

    # SOP = start of production
    def set_sop(self):
        self.sop = self.env.now
        self.statistics['order_sop'][self.id] = self.sop
        self.statistics['inv_episode'][-1][0] = self.env.now - self.statistics['inv_episode'][-1][0]
        self.statistics['inv_episode'].append([self.env.now, self.statistics['inv_episode'][-1][1] + 1])
        self.order_log.append(["sop", self.id, round(self.sop, 5), ""])

    # EOP = end of production
    def set_eop(self):
        self.eop = self.env.now
        self.statistics['order_eop'][self.id] = self.eop
        self.statistics['order_leadtime'][self.id] = self.eop - self.sop
        self.statistics['inv_episode'][-1][0] = self.env.now - self.statistics['inv_episode'][-1][0]
        self.statistics['inv_episode'].append([self.env.now, self.statistics['inv_episode'][-1][1] - 1])
        self.order_log.append(["eop", self.id, round(self.eop, 5), ""])

    # Move the job to the next process
    def set_next_step(self):
        self.actual_step += 1
        if self.actual_step > len(self.prod_steps):
            self.finished = True

    def get_next_step(self):
        return self.prod_steps[self.actual_step]

    def get_total_waiting_time(self):
        result = self.env.now - self.sop - self.time_processing - self.time_handling
        return result

    def order_processing(self):

        # Start process that ends when the job is finished by the last process
        while True:

            # Move the job to the next process
            self.set_next_step()
            
            # Check if the job is finished
            if self.finished:
                break

            # Check initial orders that are created at the beginning
            if self.id >= 0 or self in self.current_location.buffer_out:  
                
                self.order_log.append(["before_transport", self.id, round(self.env.now, 5), self.current_location.id])
                Transport.put(order=self, trans_agents=self.resources['transps'])
                
                # Transport is finished when order is placed in buffer_in of the selected destination
                yield self.transported  
                self.transported = self.env.event()
                self.order_log.append(["after_transport", self.id, round(self.env.now, 5), self.current_location.id])

            if self.get_next_step().type == 'sink':
                break

            self.order_log.append(["before_processing", self.id, round(self.env.now, 5), self.current_location.id])

            yield self.processed
            self.processed = self.env.event()

            self.order_log.append(["after_processing", self.id, round(self.env.now, 5), self.current_location.id])

        # Set the end of production
        self.set_eop()

        # Calling this procedure updates the order waiting time statistics
        self.statistics['order_waiting'][self.id] = self.get_total_waiting_time()

        # Append the order to the list of finished orders
        self.statistics['orders_done'].append(self)
        
        # Remove the order from the job shop
        self.current_location = None