import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query

import banco
from criaturas import criaturas_raras
from tempo import agora_tibia

    # CRIATURAS #
    # Nunca mudam: ficam prontas uma vez só, quando a API liga #
    # frozenset = conjunto que não muda e acha um nome sem percorrer a lista toda #
criaturas_em_ordem = sorted(criaturas_raras)
nomes_criaturas = frozenset(criaturas_raras)

    # LISTA DE MUNDOS NA MEMÓRIA #
    # Muda no máximo uma vez por dia, então só busca no banco de hora em hora #
validade_mundos = 3600

cache_mundos = {"lista": None, "nomes": frozenset(), "buscado_em": 0.0}


    # CICLO DE VIDA #
    # Abre o pool de conexões quando a API liga e fecha quando ela desliga #
@asynccontextmanager
async def ciclo_de_vida(app):

    with banco.criar_pool() as pool:
        app.state.pool = pool
        yield


    # API #
    # É por aqui que o site vai buscar os dados #
app = FastAPI(title="Tibia Boss Detector", lifespan=ciclo_de_vida)


    # FUNÇÕES #

    # FUNÇÃO : CONEXÃO DO BANCO #
    # Pega uma conexão emprestada do pool; ela volta para o pool no fim do "with" #
def conexao_banco():

    return app.state.pool.connection()

    # FUNÇÃO : MUNDOS #
    # Devolve a lista guardada; só vai ao banco se ela tiver mais de 1 hora #
def mundos_em_cache():

    vencida = time.monotonic() - cache_mundos["buscado_em"] > validade_mundos

    if cache_mundos["lista"] is None or vencida:

        with conexao_banco() as conexao:
            lista = banco.listar_mundos(conexao)

        cache_mundos["lista"] = lista
        cache_mundos["nomes"] = frozenset(m["mundo"] for m in lista)
        cache_mundos["buscado_em"] = time.monotonic()

    return cache_mundos


    # ENDEREÇOS #

    # ENDEREÇO : INÍCIO #
    # Só para testar se a API está no ar #
@app.get("/")
def inicio():

    return {"mensagem": "API do Tibia Boss Detector funcionando"}

    # ENDEREÇO : MUNDOS #
    # Lista de mundos para o seletor da tela inicial #
@app.get("/mundos")
def mundos():

    return mundos_em_cache()["lista"]

    # ENDEREÇO : CRIATURAS #
    # Lista de criaturas raras para as checkboxes da tela inicial #
@app.get("/criaturas")
def criaturas():

    return criaturas_em_ordem

    # ENDEREÇO : CONSULTA #
    # Recebe o mundo e as criaturas marcadas e devolve o semáforo de cada uma #
    # Exemplo: /consulta?mundo=Kalibra&criaturas=Yakchal&criaturas=Munster #
    # Sem criaturas marcadas, devolve todas #
@app.get("/consulta")
def consulta(mundo: str, criaturas: list[str] = Query(default=[])):

    if mundo not in mundos_em_cache()["nomes"]:
        raise HTTPException(status_code=404, detail=f"Mundo '{mundo}' não encontrado")

    desconhecidas = [c for c in criaturas if c not in nomes_criaturas]

    if desconhecidas:
        raise HTTPException(status_code=400, detail=f"Criaturas desconhecidas: {', '.join(desconhecidas)}")

    if not criaturas:
        criaturas = criaturas_em_ordem

    # Data de hoje no horário de Berlim, e não a do computador #
    hoje = agora_tibia().date()

    with conexao_banco() as conexao:
        resultado = banco.consultar_semaforo(conexao, mundo, criaturas, hoje)

    return {
        "mundo": mundo,
        "data_consulta": hoje,
        "criaturas": resultado
    }
