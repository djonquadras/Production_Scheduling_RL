import random as rd
import simpy
import numpy as np
from scipy.stats import weibull_min


# Define the shape and scale parameters
#shape = 2.5
#scale = 30


# Retorna um valor de acordo com a Função de Distribuição de Probabilidade de Weibull
def weibull(shape, scale):

    # Cria a Distribuição de Weibull
    weibull = weibull_min(shape, scale=scale)

    # Gera números aleatórios de acordo com a distribuição
    samples = weibull.rvs(size=1)

    # Retorna o valor
    return(samples[0])