import simpy
import random

# Define as constantes do sistema
NUM_PRODUTOS = 4
NUM_MAQUINAS_NIVEL1 = 5
NUM_MAQUINAS_NIVEL2 = 4
NUM_MAQUINAS_NIVEL3 = 6
TEMPO_PROD = [20, 25, 30, 35]  # Tempo de produção de cada produto
TEMPO_MANUT = [60, 80, 100, 120]  # Tempo de manutenção de cada máquina (em minutos)
PRIORIDADE_PRODUTOS = [3, 2, 1, 0]  # Prioridade de cada produto (quanto maior o número, maior a prioridade)

class SistemaProducao:
    def __init__(self, env):
        self.env = env
        self.maquinas_nivel1 = [simpy.Resource(env) for i in range(NUM_MAQUINAS_NIVEL1)]
        self.maquinas_nivel2 = [simpy.Resource(env) for i in range(NUM_MAQUINAS_NIVEL2)]
        self.maquinas_nivel3 = [simpy.Resource(env) for i in range(NUM_MAQUINAS_NIVEL3)]
        self.fila_produtos = [[] for i in range(NUM_PRODUTOS)]
        self.produzindo = False
        
    def produzir_produto(self):
        while True:
            # Seleciona o próximo produto a ser produzido (com base na prioridade)
            for i in range(NUM_PRODUTOS):
                if self.fila_produtos[PRIORIDADE_PRODUTOS[i]]:
                    produto = self.fila_produtos[PRIORIDADE_PRODUTOS[i]].pop(0)
                    break
            else:
                # Se não há mais produtos na fila, espera novos produtos chegarem
                produto = yield self.env.timeout(float('inf'))
            
            # Seleciona a primeira máquina disponível em cada nível
            maquina1 = yield self.maquinas_nivel1.index(min(self.maquinas_nivel1, key=lambda m: m.count))
            maquina2 = yield self.maquinas_nivel2.index(min(self.maquinas_nivel2, key=lambda m: m.count))
            maquina3 = yield self.maquinas_nivel3.index(min(self.maquinas_nivel3, key=lambda m: m.count))
            
            # Produz o produto nas três máquinas
            with self.maquinas_nivel1[maquina1], self.maquinas_nivel2[maquina2], self.maquinas_nivel3[maquina3]:
                print(f'{self.env.now:.2f}: Produzindo {produto} nas máquinas {maquina1}, {maquina2} e {maquina3}.')
                yield self.env.timeout(sum(TEMPO_PROD[produto]))
                
            # Aguarda um tempo aleatório até a próxima manutenção das máquinas
            yield self.env.timeout(random.uniform(0.9, 1.1) * TEMPO_MANUT[maquina1])
            yield self.env.timeout(random.uniform(0.9, 1.1) * TEMPO_MANUT[maquina2])
            yield self.env.timeout(random.uniform(0.9, 1.1) * TEMPO_MANUT[maquina3])
            
    def adicionar_produto(self, produto):
        # Adiciona o produto na fila correspondente
        self.fila_produtos[produto].append(produto)
        print(f'{self.env.now:.2f}: Adicionado produto {produto} na fila.')
        
        if not self.produzindo:
            # Inicia a produção se não há nada sendo produzido atualmente
            self.produzindo = True
            self.env.process(self.produzir_produto())
            
# Cria o ambiente de simulação
env = simpy.Environment()
sistema = SistemaProducao(env)

# Adiciona alguns produtos à fila (com prioridades diferentes)
sistema.adicionar_produto(0)
sistema.adicionar_produto(2)
sistema.adicionar_produto(3)
sistema.adicionar_produto(1)

# Roda a simulação por 1000 minutos
env.run(until=1000)
