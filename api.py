from fastapi import FastAPI, HTTPException, Query

import banco
from criaturas import criaturas_raras
from tempo import agora_tibia

    # API #
    # É por aqui que o site vai buscar os dados #
app = FastAPI(title="Tibia Boss Detector")


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

    return banco.listar_mundos()

    # ENDEREÇO : CRIATURAS #
    # Lista de criaturas raras para as checkboxes da tela inicial #
@app.get("/criaturas")
def criaturas():

    return sorted(criaturas_raras)

    # ENDEREÇO : CONSULTA #
    # Recebe o mundo e as criaturas marcadas e devolve o semáforo de cada uma #
    # Exemplo: /consulta?mundo=Kalibra&criaturas=Yakchal&criaturas=Munster #
    # Sem criaturas marcadas, devolve todas #
@app.get("/consulta")
def consulta(mundo: str, criaturas: list[str] = Query(default=[])):

    nomes_mundos = [m["mundo"] for m in banco.listar_mundos()]

    if mundo not in nomes_mundos:
        raise HTTPException(status_code=404, detail=f"Mundo '{mundo}' não encontrado")

    desconhecidas = [c for c in criaturas if c not in criaturas_raras]

    if desconhecidas:
        raise HTTPException(status_code=400, detail=f"Criaturas desconhecidas: {', '.join(desconhecidas)}")

    if not criaturas:
        # O banco precisa de uma lista, e criaturas_raras é uma tupla #
        criaturas = list(criaturas_raras)

    # Data de hoje no horário de Berlim, e não a do computador #
    hoje = agora_tibia().date()

    return {
        "mundo": mundo,
        "data_consulta": hoje,
        "criaturas": banco.consultar_semaforo(mundo, criaturas, hoje)
    }
