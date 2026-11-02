from contextlib import nullcontext

import pytest
from fastapi.testclient import TestClient

import api
import banco
from api import app

    # CLIENTE DE TESTE #
    # Faz pedidos para a API sem precisar ligar o servidor #
cliente = TestClient(app)


    # PREPARAÇÃO : API SEM BANCO #
    # O pool é trocado por uma conexão vazia (nullcontext) e a lista de mundos #
    # guardada na memória é zerada, para um teste não interferir no outro #
    # Os mundos que existem são só Kalibra e Antica; a função anota cada busca no banco #
@pytest.fixture(autouse=True)
def api_sem_banco(monkeypatch):

    buscas = []

    def listar_falso(conexao):
        buscas.append(1)
        return [{"mundo": "Antica", "regiao": "Europe"}, {"mundo": "Kalibra", "regiao": "Europe"}]

    monkeypatch.setattr(api, "conexao_banco", nullcontext)
    monkeypatch.setattr(api, "cache_mundos", {"lista": None, "nomes": frozenset(), "buscado_em": 0.0})
    monkeypatch.setattr(banco, "listar_mundos", listar_falso)

    return buscas


    # TESTES #
    # O banco é trocado por funções falsas (monkeypatch), então os testes não precisam do PostgreSQL #

    # TESTE : MUNDO QUE NÃO EXISTE #
    # Tem que responder 404 (não encontrado) #
def test_consulta_mundo_inexistente():

    resposta = cliente.get("/consulta", params={"mundo": "Mundo Falso"})

    assert resposta.status_code == 404


    # TESTE : CRIATURA QUE NÃO É RARA #
    # Tem que responder 400 (pedido errado) e dizer qual criatura está errada #
def test_consulta_criatura_desconhecida():

    resposta = cliente.get("/consulta", params={"mundo": "Kalibra", "criaturas": ["Dragon"]})

    assert resposta.status_code == 400
    assert "Dragon" in resposta.json()["detail"]


    # TESTE : CONSULTA SEM CRIATURAS MARCADAS #
    # Sem criaturas, a API tem que buscar todas as criaturas raras #
def test_consulta_sem_criaturas_busca_todas(monkeypatch):

    pedidos = []

    def consultar_falso(conexao, mundo, criaturas, hoje):
        pedidos.append(criaturas)
        return []

    monkeypatch.setattr(banco, "consultar_semaforo", consultar_falso)

    resposta = cliente.get("/consulta", params={"mundo": "Kalibra"})

    assert resposta.status_code == 200
    assert len(pedidos[0]) == 29


    # TESTE : CONSULTA SEM MUNDO #
    # O mundo é obrigatório: sem ele a API responde 422 (faltou informação) #
def test_consulta_sem_mundo():

    resposta = cliente.get("/consulta")

    assert resposta.status_code == 422


    # TESTE : LISTA DE MUNDOS NA MEMÓRIA #
    # Vários pedidos seguidos: o banco só é consultado na primeira vez #
def test_mundos_busca_no_banco_uma_vez_so(api_sem_banco):

    cliente.get("/mundos")
    cliente.get("/mundos")
    cliente.get("/consulta", params={"mundo": "Mundo Falso"})

    assert len(api_sem_banco) == 1


    # TESTE : LISTA DE MUNDOS VENCIDA #
    # Depois de 1 hora, a lista é buscada de novo no banco #
def test_mundos_busca_de_novo_depois_de_1_hora(api_sem_banco):

    cliente.get("/mundos")

    api.cache_mundos["buscado_em"] -= api.validade_mundos + 1

    cliente.get("/mundos")

    assert len(api_sem_banco) == 2


    # TESTE : CRIATURAS EM ORDEM #
def test_criaturas_em_ordem_alfabetica():

    resposta = cliente.get("/criaturas").json()

    assert len(resposta) == 29
    assert resposta == sorted(resposta)
