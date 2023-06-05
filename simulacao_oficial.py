import simpy
import pandas as pd
import random

# Função para simular o sistema produtivo
def sistema_produtivo(env, dataset_ordens, dataset_maquinas):
    maquinas = {}
    fila_step1 = [simpy.PriorityResource(env) for _ in range(60)]
    fila_step2 = [simpy.PriorityResource(env) for _ in range(2)]
    fila_step3 = [simpy.PriorityResource(env) for _ in range(3)]
    tempo_setup = 40
    
    def processar_produto(produto):
        id_material = produto['id_material']
        tipo_material = produto['tipo_material']
        tempo_processamento_m1 = produto['tempo_processamento_maquina1']
        tempo_processamento_m2 = produto['tempo_processamento_maquina2']
        tempo_processamento_m3 = produto['tempo_processamento_maquina3']
        maquina_step1 = produto['maquina_step1']
        maquina_step2 = produto['maquina_step2']
        maquina_step3 = produto['maquina_step3']
        prioridade_m1 = produto['prioridade_m1']
        prioridade_m2 = produto['prioridade_m2']
        prioridade_m3 = produto['prioridade_m3']
        
        
        with fila_step1[maquina_step1].request(priority=prioridade_m1) as req:
            yield req
            # Verifica Necessidade de setup
            if maquinas[maquina_step1]['tipo_material'] != tipo_material:
                yield env.timeout(tempo_setup)
                maquinas[maquina_step1]['tipo_material'] = tipo_material
            yield env.timeout(tempo_processamento_m1)
            
        with fila_step2[maquina_step2].request(priority=prioridade_m2) as req:
            yield req
            # Verifica Necessidade de setup
            if maquinas[maquina_step2]['tipo_material'] != tipo_material:
                yield env.timeout(tempo_setup)
                maquinas[maquina_step2]['tipo_material'] = tipo_material
            yield env.timeout(tempo_processamento_m2)
                
        with fila_step3[maquina_step3].request(priority=prioridade_m3) as req:
            yield req
            # Verifica Necessidade de setup
            if maquinas[maquina_step3]['tipo_material'] != tipo_material:
                yield env.timeout(tempo_setup)
                maquinas[maquina_step3]['tipo_material'] = tipo_material
            yield env.timeout(tempo_processamento_m3)


    # Função para lidar com a quebra das máquinas
    def quebra_maquina(maquina):
        tempo_vida = maquina['tempo_vida']
        minuto_preventiva = maquina['minuto_preventiva']
        tempo_preventiva1 = maquina['tempo_preventiva1']
        tempo_preventiva2 = maquina['tempo_preventiva2']
        tempo_corretiva = maquina['tempo_corretiva']
        tipo_manutencao = maquina['tipo_manutencao']
        
        while True:
            # Espera até que a máquina quebre
            yield env.timeout(tempo_vida)
            
            # Realiza a manutenção corretiva
            print(f"Quebra da máquina {maquina['id_maquina']} no tempo {env.now}")
            yield env.timeout(tempo_corretiva)
            
            # Realiza a manutenção preventiva
            if env.now >= minuto_preventiva:
                if tipo_manutencao == 1:
                    maquina['tempo_vida'] *= 1.25
                    yield env.timeout(tempo_preventiva1)
                elif tipo_manutencao == 2:
                    maquina['tempo_vida'] = maquina['tempo_vida_inicial']
                    yield env.timeout(tempo_preventiva2)
            
    # Cria as máquinas
    for _, maquina in dataset_maquinas.iterrows():
        maquinas[maquina['id_maquina']] = {
            'tipo_material': None,
            'tempo_vida': maquina['tempo_vida'],
            'tempo_vida_inicial': maquina['tempo_vida'],
            'minuto_preventiva': maquina['minuto_preventiva'],
            'tempo_preventiva1': maquina['tempo_preventiva1'],
            'tempo_preventiva2': maquina['tempo_preventiva2'],
            'tempo_corretiva': maquina['tempo_corretiva'],
            'tipo_manutencao': maquina['tipo_manutencao']
        }
        
        env.process(quebra_maquina(maquinas[maquina['id_maquina']]))
        
    # Cria as ordens de produção
    for _, ordem in dataset_ordens.iterrows():
        yield env.timeout(random.uniform(0, 10))  # Intervalo de chegada dos produtos
        env.process(processar_produto(ordem))

# Carrega os datasets
dataset_ordens = pd.read_csv('dataset_ordens.csv')
dataset_maquinas = pd.read_csv('dataset_maquinas.csv')

# Inicia a simulação
env = simpy.Environment()
env.process(sistema_produtivo(env, dataset_ordens, dataset_maquinas))
env.run(until=1000)  # Tempo total da simulação
