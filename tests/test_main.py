from datetime import datetime, date
from zoneinfo import ZoneInfo

import requests

import main
from main import consultar_api, criar_registros, data_hoje_tibia


    # TESTES #

    # TESTE : IMPORTAR MAIN #
    # Confere se o main.py carrega sem erro e se a função de consulta existe #
def test_importar_main():

    assert callable(main.consultar_api)


    # TESTE : CRIAR REGISTROS COM CRIATURAS AUSENTES #
    # A API devolve só o Yeti. O registro tem que ter o Yeti com as kills certas #
    # e a Midnight Panther com 0 kills e marcada como não encontrada na API #
    # Os dois registros guardam o timestamp que veio da API #
def test_criar_registros_inclui_criaturas_ausentes():

    dados = {
        "information": {
            "timestamp": "2026-10-15T09:00:00Z"
        },
        "killstatistics": {
            "entries": [
                {
                    "race": "Yeti",
                    "last_day_killed": 2,
                    "last_week_killed": 5
                }
            ]
        }
    }

    criaturas_raras = ["Yeti", "Midnight Panther"]

    registros = criar_registros(
        dados,
        criaturas_raras,
        "2026-10-14",
        "2026-10-15",
        "Kalibra"
    )

    assert len(registros) == 2

    yeti = next(r for r in registros if r["criatura"] == "Yeti")
    pantera = next(r for r in registros if r["criatura"] == "Midnight Panther")

    assert yeti["encontrada_na_api"] is True
    assert yeti["kills_24h"] == 2
    assert yeti["kills_7d"] == 5

    assert pantera["encontrada_na_api"] is False
    assert pantera["kills_24h"] == 0
    assert pantera["kills_7d"] == 0

    assert yeti["timestamp_api"] == "2026-10-15T09:00:00Z"
    assert pantera["timestamp_api"] == "2026-10-15T09:00:00Z"


    # TESTE : DATA DE HOJE NO HORÁRIO DE BERLIM #
    # Simula 23:30 de Brasília. Em Berlim já é o dia seguinte (03:30), #
    # então a data tem que ser a de Berlim e não a do computador #
def test_data_hoje_tibia_usa_horario_de_berlim(monkeypatch):

    brasilia = ZoneInfo("America/Sao_Paulo")
    agora_brasilia = datetime(2026, 10, 25, 23, 30, tzinfo=brasilia)

    class DatetimeFalso:
        @staticmethod
        def now(fuso):
            return agora_brasilia.astimezone(fuso)

    monkeypatch.setattr(main, "datetime", DatetimeFalso)

    assert data_hoje_tibia() == date(2026, 10, 26)


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
