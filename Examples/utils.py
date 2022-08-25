import random as rd
import simpy

class order:
  """
  The production orders that will be produced in the factory.
  ``code`` differentiate the production orders.
  ``steelType`` classificate the order regarding three different steel types
  ``startDate`` is when the demand arrives
  ``dueDate`` is the time limit to produce the order
  ``demand`` is the amount that must be produced. 
  """
  def __init__(self,code, needStove, startDate, dueDate, demand):
    self.code = code
    self.startDate = startDate
    self.dueDate = dueDate
    self.demand = demand
    self.totalProcessingTime = 0
    self.stampingTime = 0
    self.machine = 0
    self.priority = 0
    self.needStove = needStove


def time_per_part(PT_MEAN, PT_SIGMA):
  """Return actual processing time for a concrete part."""
  return rd.normalvariate(PT_MEAN, PT_SIGMA)

def time_to_failure(BREAK_MEAN):
  """Return time until next failure for a machine."""
  return rd.expovariate(BREAK_MEAN)


class Machine(object):
    """A machine produces the productionOrders and may get broken.
    If it breaks, it requests a *maintenance* and continues the production
    after the it is repaired.
    A machine has a *name* and a number of *parts_made* thus far.
    """
    def __init__(self, env, name, repairman, WORKING_HOUR):
        self.env = env
        self.name = name
        self.parts_made = 0
        self.broken = False
        self.inWorkingJourney = True
        # Start "working" and "break_machine" processes for this machine.
        self.process = env.process(self.working(repairman))
        env.process(self.break_machine())
    
    def working(self, repairman, REPAIR_TIME):
        """Produce parts as long as the simulation runs.
        While making a part, the machine may break multiple times.
        Request a repairman when this happens.
        """
        while True:
            # Start making a new part
            done_in = time_per_part()
            while done_in:
                try:
                    # Working on the part
                    start = self.env.now
                    yield self.env.timeout(done_in)
                    done_in = 0 # Set to 0 to exit while loop.
                except simpy.Interrupt:
                    self.broken = True
                    done_in -= self.env.now - start # How much time left?
                    
                    # Request a repairman. This will preempt its "other_job".
                    with repairman.request(priority=1) as req:
                        yield req
                        yield self.env.timeout(REPAIR_TIME)
                    self.broken = False
            
            # Part is done.
            self.parts_made += 1

    def break_machine(self):
        """Break the machine every now and then."""
        while True:
            yield self.env.timeout(time_to_failure())
            if not self.broken:
                # Only break the machine if it is currently working.
                self.process.interrupt()
            
