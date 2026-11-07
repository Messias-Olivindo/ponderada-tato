"""Versao 3 da A4: como a versao 2, mas o produtor faz wait(mutex) ANTES de wait(vazio).

Parametros: N=3 posicoes no buffer circular, 20.000 amostras (0..19999),
3 execucoes em sequencia. Produtor = thread do sensor, consumidor = thread
do motor. Uma thread principal vigia: 1 s sem o consumidor receber nada
conta como travamento.
Como rodar: cd ponderada/codigo && python3 versao3.py
Saida: cabecalho e, por execucao, uma linha
RESULTADO versao=.. execucao=.. produzidas=.. consumidas=.. perdidas=..
duplicadas=.. travou=..
"""
import os
import threading
import time

N = 3             # tamanho do buffer circular
AMOSTRAS = 20000  # amostras numeradas 0..19999
EXECUCOES = 3     # execucoes em sequencia
TIMEOUT = 1.0     # segundos sem o consumidor receber nada = travamento
DESC = "ordem trocada"


def novo_estado():
    """Cria o estado compartilhado de uma execucao.

    Parametros: nenhum.
    Retorno: dict com buffer, indices entra/sai, ids recebidos, contador de
    produzidas, instante da ultima recepcao, Event de parada, semaforos."""
    e = {"buf": [None] * N, "entra": 0, "sai": 0, "recebidas": [],
         "produzidas": 0, "ultimo": time.time(), "parar": threading.Event()}
    e["vazio"] = threading.Semaphore(N)
    e["cheio"] = threading.Semaphore(0)
    e["mutex"] = threading.Semaphore(1)
    return e


def produtor(e):
    """Thread do sensor (produtora) da versao 3.

    Parametros: e, dict de estado compartilhado (com os semaforos).
    Retorno: nenhum.
    Funcionamento: como a versao 2, mas wait(mutex) ANTES de wait(vazio): com o buffer cheio
    segura o mutex esperando vazio, e o consumidor precisa do mutex (deadlock)."""
    for i in range(AMOSTRAS):
        e["mutex"].acquire()  # ordem trocada: mutex ANTES de vazio
        e["vazio"].acquire()
        e["buf"][e["entra"]] = i
        e["entra"] = (e["entra"] + 1) % N
        e["produzidas"] += 1
        e["mutex"].release()
        e["cheio"].release()


def consumidor(e):
    """Thread do motor (consumidora) da versao 3.

    Parametros: e, dict de estado compartilhado (com os semaforos).
    Retorno: nenhum.
    Funcionamento: wait(cheio), wait(mutex), le buf[sai], avanca sai,
    signal(mutex), signal(vazio). Atualiza e["ultimo"] a cada leitura."""
    for _ in range(AMOSTRAS):
        e["cheio"].acquire()
        e["mutex"].acquire()
        e["recebidas"].append(e["buf"][e["sai"]])
        e["ultimo"] = time.time()
        e["sai"] = (e["sai"] + 1) % N
        e["mutex"].release()
        e["vazio"].release()


def calcular(e):
    """Calcula as métricas de uma execução (chamada pela thread principal).

    Parâmetros: e, dict de estado da execução.
    Retorno: tupla (produzidas, consumidas, perdidas, duplicadas).
    Funcionamento: perdidas = ids produzidos que o consumidor nunca recebeu;
    duplicadas = repetições de ids recebidos (total recebido - ids distintos)."""
    rec = list(e["recebidas"])
    distintos = set(rec)
    produzidos = set(range(e["produzidas"]))
    return (e["produzidas"], len(rec), len(produzidos - distintos),
            len(rec) - len(distintos))


def executar(k):
    """Roda uma execução completa e imprime a linha RESULTADO.

    Parâmetros: k, número da execução (1..3).
    Retorno: nenhum.
    Funcionamento: sobe produtor e consumidor (daemon), vigia até o consumidor
    terminar ou ficar TIMEOUT segundos sem receber nada (travou), manda parar
    e imprime as métricas."""
    e = novo_estado()
    p = threading.Thread(target=produtor, args=(e,), daemon=True)
    c = threading.Thread(target=consumidor, args=(e,), daemon=True)
    e["ultimo"] = time.time()
    p.start()
    c.start()
    travou = False
    while c.is_alive():  # a thread principal vigia
        c.join(0.05)
        if c.is_alive() and time.time() - e["ultimo"] > TIMEOUT:
            travou = True
            break
    e["parar"].set()  # faz os loops de espera ocupada saírem
    prod, cons, perd, dup = calcular(e)
    print(f"RESULTADO versao=3 execucao={k} produzidas={prod} "
          f"consumidas={cons} perdidas={perd} duplicadas={dup} "
          f"travou={'sim' if travou else 'nao'}", flush=True)


def main():
    """Imprime o cabeçalho e faz as 3 execuções em sequência.

    Parâmetros: nenhum. Retorno: nenhum."""
    print(f"Versao 3 ({DESC}) | N={N} | amostras={AMOSTRAS}", flush=True)
    for k in range(1, EXECUCOES + 1):
        executar(k)
    os._exit(0)  # encerra mesmo com threads daemon bloqueadas


if __name__ == "__main__":
    main()
