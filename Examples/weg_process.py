import simpy

class weg(object):
    """
    Creates the WEG production line
    """

    def __init__(self, env, num_stampingMachines):
        self.env = env
        self.stampingMachine = simpy.PriorityResource(env, num_stampingMachines) 

    def stamping(self, order):
        """
        The Stamping process. 
        """
        yield self.env.timeout(order.stampingTime)

    def stove(self):
        """
        The Stove process.
        """
        yield self.env.timeout(12*60)

    def work_journey(self):
        """
        Defines the work journey.
        """
        while True:
            yield self.env.timeout(24 - self.WORKING_HOUR)
            self.process.interrupt()
