# Libraries
import simpy
import sklearn as skl
import matplotlib as mpl
import time 
import random as rd
import utils as dj
import weg_process as weg
import pandas as pd

# Create the environment
env = simpy.Environment()

# Random seed to replicable experiments
rd.seed(123)

# Production Orders
order = dj.order(code = 111, steelType = "A", startDate=0, dueDate=10, demand=50)
order.stampingTime = 15
order.needStove = True

# Reading Data
listOfOrders = list()
data = pd.read_excel("data.xlsx", engine = "openpyxl")
for i in data.index:
    ord = dj.order(data.productionOrder[1],
                    data.s)

print(data.startDate[0])
#print(data.head())



# # The source
# def source(env, number, interval, counter):
#     """Source generates customers randomly"""
#     for i in range(number):
#         c = customer(env, 'Customer%02d' % i, counter, time_in_bank=12.0)
#         env.process(c)
#         t = random.expovariate(1.0 / interval)
#         yield env.timeout(t)



# # The jobs

# def jobs(env, wegJob, order):
#     "The jobs process"
#     while True:
#         print("Job Started")
#         with wegJob.stampingMachine.request() as req:
#             yield req
#             yield env.process(wegJob.stamping(order))
#             print(f"Job left stamping machine at {env.now}")

#         if order.needStove:
#             print("order needed stove")
#             yield env.process(wegJob.stove())
#             print(f"order left line at {env.now}")



# env.process(jobs(env, weg.weg(env,3), order))
# # Execute!
# env.run(until=4500)

    


