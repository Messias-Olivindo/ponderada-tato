"""Versao 1 da A4: produtor/consumidor SEM sincronizacao (contador compartilhado, espera ocupada).

Parametros: N=3 posicoes no buffer circular, 20.000 amostras (0..19999),
3 execucoes em sequencia. Produtor = thread do sensor, consumidor = thread
do motor. Uma thread principal vigia: 1 s sem o consumidor receber nada
conta como travamento.
Como rodar: cd ponderada/codigo && python3 versao1.py
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
DESC = "sem sincronizacao"


def novo_estado():
    """Cria o estado compartilhado de uma execucao.

    Parametros: nenhum.
    Retorno: dict com buffer, indices entra/sai, ids recebidos, contador de
    produzidas, instante da ultima recepcao, Event de parada, contador ocupadas."""
    e = {"buf": [None] * N, "entra": 0, "sai": 0, "recebidas": [],
         "produzidas": 0, "ultimo": time.time(), "parar": threading.Event()}
    e["ocupadas"] = 0  # contador compartilhado de posicoes ocupadas
    return e


def produtor(e):
    """Thread do sensor (produtora) da versao 1, sem sincronizacao.

    Parametros: e, dict de estado compartilhado. Retorno: nenhum.
    Funcionamento: espera (espera ocupada) o buffer sair de cheio, grava em
    buf[entra], avanca entra e incrementa `ocupadas` em tres passos (le,
    sleep(0), escreve): essa e a regiao critica, sem protecao."""
    for i in range(AMOSTRAS):
        while e["ocupadas"] == N:  # cheio: espera ocupada
            if e["parar"].is_set():
                return
        e["buf"][e["entra"]] = i
        e["entra"] = (e["entra"] + 1) % N
        e["produzidas"] += 1
        tmp = e["ocupadas"]
        time.sleep(0)  # simula interrupcao no pior momento
        e["ocupadas"] = tmp + 1


def consumidor(e):
    """Thread do motor (consumidora) da versao 1, sem sincronizacao.

    Parametros: e, dict de estado compartilhado. Retorno: nenhum.
    Funcionamento: espera (espera ocupada) haver amostra, le buf[sai], avanca
    sai e decrementa `ocupadas` em tres passos (le, sleep(0), escreve).
    Atualiza e["ultimo"] a cada leitura (usado pela principal)."""
    for _ in range(AMOSTRAS):
        while e["ocupadas"] == 0:  # vazio: espera ocupada
            if e["parar"].is_set():
                return
        e["recebidas"].append(e["buf"][e["sai"]])
        e["ultimo"] = time.time()
        e["sai"] = (e["sai"] + 1) % N
        tmp = e["ocupadas"]
        time.sleep(0)  # simula interrupcao no pior momento
        e["ocupadas"] = tmp - 1


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
    print(f"RESULTADO versao=1 execucao={k} produzidas={prod} "
          f"consumidas={cons} perdidas={perd} duplicadas={dup} "
          f"travou={'sim' if travou else 'nao'}", flush=True)


def main():
    """Imprime o cabeçalho e faz as 3 execuções em sequência.

    Parâmetros: nenhum. Retorno: nenhum."""
    print(f"Versao 1 ({DESC}) | N={N} | amostras={AMOSTRAS}", flush=True)
    for k in range(1, EXECUCOES + 1):
        executar(k)
    os._exit(0)  # encerra mesmo com threads daemon bloqueadas


if __name__ == "__main__":
    main()
