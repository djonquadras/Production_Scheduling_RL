import simpy
import random

class JobShopSimulation:
    def __init__(self, num_orders, num_machines_stage1, num_machines_stage2, num_machines_stage3):
        self.env = simpy.Environment()
        self.num_orders = num_orders
        self.num_machines_stage1 = num_machines_stage1
        self.num_machines_stage2 = num_machines_stage2
        self.num_machines_stage3 = num_machines_stage3
        self.setup_times = self.generate_setup_times()
        self.processing_times = self.generate_processing_times()
        self.maintenance_intervals = self.generate_maintenance_intervals()

    def generate_setup_times(self):
        # Generate setup times for each machine
        setup_times = {}
        for machine in range(self.num_machines_stage1):
            setup_times[machine] = random.randint(1, 10)
        for machine in range(self.num_machines_stage2):
            setup_times[machine + self.num_machines_stage1] = random.randint(1, 10)
        for machine in range(self.num_machines_stage3):
            setup_times[machine + self.num_machines_stage1 + self.num_machines_stage2] = random.randint(1, 10)
        return setup_times

    def generate_processing_times(self):
        # Generate processing times for each machine
        processing_times = {}
        for machine in range(self.num_machines_stage1):
            processing_times[machine] = random.randint(10, 20)
        for machine in range(self.num_machines_stage2):
            processing_times[machine + self.num_machines_stage1] = random.randint(10, 20)
        for machine in range(self.num_machines_stage3):
            processing_times[machine + self.num_machines_stage1 + self.num_machines_stage2] = random.randint(10, 20)
        return processing_times

    def generate_maintenance_intervals(self):
        # Generate maintenance intervals for each machine
        maintenance_intervals = {}
        for machine in range(self.num_machines_stage1):
            maintenance_intervals[machine] = random.randint(10, 20)
        for machine in range(self.num_machines_stage2):
            maintenance_intervals[machine + self.num_machines_stage1] = random.randint(10, 20)
        for machine in range(self.num_machines_stage3):
            maintenance_intervals[machine + self.num_machines_stage1 + self.num_machines_stage2] = random.randint(10, 20)
        return maintenance_intervals

    def order_process(self, order):
        yield self.env.timeout(order.priority)  # Priority-based delay

        # Stage 1: Machine selection and setup
        stage1_machine = random.randint(0, self.num_machines_stage1 - 1)
        setup_time = self.setup_times[stage1_machine]
        yield self.env.timeout(setup_time)

        # Stage 2: Machine selection and setup
        stage2_machine = random.randint(0, self.num_machines_stage2 - 1)
        setup_time = self.setup_times[stage2_machine + self.num_machines_stage1]
        yield self.env.timeout(setup_time)

        # Stage 3: Machine selection and setup
        stage3_machine = random.randint(0, self.num_machines_stage3 - 1)
        setup_time = self.setup_times[stage3_machine + self.num_machines_stage1 + self.num_machines_stage2]
        yield self.env.timeout(setup_time)

        # Processing time in each stage
        processing_time_stage1 = self.processing_times[stage1_machine]
        processing_time_stage2 = self.processing_times[stage2_machine + self.num_machines_stage1]
        processing_time_stage3 = self.processing_times[stage3_machine + self.num_machines_stage1 + self.num_machines_stage2]

        # Process the order in each stage
        yield self.env.timeout(processing_time_stage1)
        yield self.env.timeout(processing_time_stage2)
        yield self.env.timeout(processing_time_stage3)

    def machine_maintenance(self, machine):
        # Perform machine maintenance based on machine type
        maintenance_interval = self.maintenance_intervals[machine]
        yield self.env.timeout(maintenance_interval)

    def run_simulation(self):
        for i in range(self.num_orders):
            order = {
                'order_id': i,
                'priority': random.randint(1, 10)
            }
            self.env.process(self.order_process(order))

        # Machine maintenance processes
        for machine in range(self.num_machines_stage1):
            self.env.process(self.machine_maintenance(machine))
        for machine in range(self.num_machines_stage2):
            self.env.process(self.machine_maintenance(machine + self.num_machines_stage1))
        for machine in range(self.num_machines_stage3):
            self.env.process(self.machine_maintenance(machine + self.num_machines_stage1 + self.num_machines_stage2))

        self.env.run(until=self.num_orders)


# Example usage
simulation = JobShopSimulation(num_orders=100, num_machines_stage1=10, num_machines_stage2=15, num_machines_stage3=30)
simulation.run_simulation()
