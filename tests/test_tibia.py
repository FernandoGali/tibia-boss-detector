from datetime import datetime, date, timezone

import requests

from tempo import data_atividade, fuso_tibia
from tibia import calcular_resumo, consultar_api


    # TESTES #

    # TESTE : API RESPONDE COM ERRO #
    # Simula a API devolvendo status 404. A consulta tem que retornar None #
    # em vez de quebrar o programa #
def test_consultar_api_status_erro(monkeypatch):

    class RespostaFalsa:
        status_code = 404

    monkeypatch.setattr(requests, "get", lambda url, timeout: RespostaFalsa())

    assert consultar_api("Kalibra") is None


    # TESTE : FALHA DE CONEXÃO COM A API #
    # Simula a API sem responder (timeout). A consulta tem que retornar None #
    # em vez de quebrar o programa #
def test_consultar_api_falha_conexao(monkeypatch):

    def conexao_falha(url, timeout):
        raise requests.exceptions.Timeout()

    monkeypatch.setattr(requests, "get", conexao_falha)

    assert consultar_api("Kalibra") is None


    # TESTE : MUNDO NOVO SEM KILL STATISTICS #
    # No dia do lançamento a API responde 200, mas com a lista de mortes vazia (null) #
    # A consulta tem que retornar None, como numa falha, e tentar de novo depois #
def test_consultar_api_mundo_novo_sem_kill_statistics(monkeypatch):

    class RespostaFalsa:
        status_code = 200

        def json(self):
            return {"killstatistics": {"world": "Quirina", "entries": None}}

    monkeypatch.setattr(requests, "get", lambda url, timeout: RespostaFalsa())

    assert consultar_api("Quirina") is None


    # TESTE : CALCULAR RESUMO #
    # Soma as kills de 24h e de 7 dias de todas as criaturas #
def test_calcular_resumo_soma_as_kills():

    dados = {
        "killstatistics": {
            "entries": [
                {"race": "Dragon", "last_day_killed": 10, "last_week_killed": 70},
                {"race": "Yeti", "last_day_killed": 1, "last_week_killed": 2}
            ]
        }
    }

    resumo = calcular_resumo(dados)

    assert resumo["kills_24h_total"] == 11
    assert resumo["kills_7d_total"] == 72


    # TESTE : DATA DA ATIVIDADE NA HORA DA ATUALIZAÇÃO #
    # Atualização detectada às 04:05 de Berlim do dia 26 = mortes do dia 25 #
def test_data_atividade_detectada_de_madrugada():

    horario = datetime(2026, 10, 26, 4, 5, tzinfo=fuso_tibia)

    assert data_atividade(horario) == date(2026, 10, 25)


    # TESTE : DATA DA ATIVIDADE DETECTADA DEPOIS DA MEIA-NOITE #
    # Computador desligado: a atualização do dia 26 só foi detectada à 01:00 do dia 27 #
    # Continua sendo a atualização do dia 26, então as mortes são do dia 25 #
def test_data_atividade_detectada_depois_da_meia_noite():

    horario = datetime(2026, 10, 27, 1, 0, tzinfo=fuso_tibia)

    assert data_atividade(horario) == date(2026, 10, 25)


    # TESTE : DATA DA ATIVIDADE COM HORÁRIO EM UTC #
    # O banco devolve os horários em UTC. 03:05 UTC = 04:05 de Berlim no inverno #
def test_data_atividade_com_horario_utc():

    horario = datetime(2026, 10, 26, 3, 5, tzinfo=timezone.utc)

    assert data_atividade(horario) == date(2026, 10, 25)
