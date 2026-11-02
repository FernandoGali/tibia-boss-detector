from fastapi.testclient import TestClient

import banco
from api import app

    # CLIENTE DE TESTE #
    # Faz pedidos para a API sem precisar ligar o servidor #
cliente = TestClient(app)


    # TESTES #
    # O banco é trocado por funções falsas (monkeypatch), então os testes não precisam do PostgreSQL #

    # TESTE : MUNDO QUE NÃO EXISTE #
    # Tem que responder 404 (não encontrado) #
def test_consulta_mundo_inexistente(monkeypatch):

    monkeypatch.setattr(banco, "listar_mundos", lambda: [{"mundo": "Kalibra", "regiao": "Europe"}])

    resposta = cliente.get("/consulta", params={"mundo": "Mundo Falso"})

    assert resposta.status_code == 404


    # TESTE : CRIATURA QUE NÃO É RARA #
    # Tem que responder 400 (pedido errado) e dizer qual criatura está errada #
def test_consulta_criatura_desconhecida(monkeypatch):

    monkeypatch.setattr(banco, "listar_mundos", lambda: [{"mundo": "Kalibra", "regiao": "Europe"}])

    resposta = cliente.get("/consulta", params={"mundo": "Kalibra", "criaturas": ["Dragon"]})

    assert resposta.status_code == 400
    assert "Dragon" in resposta.json()["detail"]


    # TESTE : CONSULTA SEM CRIATURAS MARCADAS #
    # Sem criaturas, a API tem que buscar todas as criaturas raras #
def test_consulta_sem_criaturas_busca_todas(monkeypatch):

    pedidos = []

    def consultar_falso(mundo, criaturas, hoje):
        pedidos.append(criaturas)
        return []

    monkeypatch.setattr(banco, "listar_mundos", lambda: [{"mundo": "Kalibra", "regiao": "Europe"}])
    monkeypatch.setattr(banco, "consultar_semaforo", consultar_falso)

    resposta = cliente.get("/consulta", params={"mundo": "Kalibra"})

    assert resposta.status_code == 200
    assert len(pedidos[0]) == 29


    # TESTE : CONSULTA SEM MUNDO #
    # O mundo é obrigatório: sem ele a API responde 422 (faltou informação) #
def test_consulta_sem_mundo():

    resposta = cliente.get("/consulta")

    assert resposta.status_code == 422
