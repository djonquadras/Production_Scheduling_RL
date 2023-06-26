# Optimization for a Textile Job-Shop

Simulation and otimization for a Industrial Textil Procuditon System using Reinforcement Learning. This framework aims to integrate the order dispatching and maintenance scheduling for the system.

## Features

The simulation model covers the following features (production.envs.initialize_env.py):

- **Machines:** the system is formed by 59 parallel machines. 
- **Orders:** To do.

The **Reinforcement Learning** is based on the Tensorforce library. Problem-specific configurations for the order dispatching task are the following (initialize_env.py):

- State representation, i.e. which information elements are part of the state vector
- Reward function (incl. consideration of multiple objective functions and weighted reward functions according to action subset type)
- Action representation, i.e. which actions are allowed (e.g., "idling" action) and type of mapping of discrete action number to dispatching decisions
- Episode definition and limit
- RL-specific parameters such as learning rate, discount rate, neural network configuration etc. are defined in the Tensorforce agent configuration file