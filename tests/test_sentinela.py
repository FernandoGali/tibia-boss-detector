from datetime import datetime

import banco
import sentinela
from sentinela import escolher_sentinelas, verificar_mudanca
from tibia import fuso_tibia


    # TESTES #

    # TESTE : ESCOLHER SENTINELAS #
    # Tem que pegar os 2 mundos mais cheios da Europa e só 1 da Oceania #
def test_escolher_sentinelas_pega_os_mais_cheios():

    mundos = [
        {"name": "Antica", "location": "Europe", "players_online": 700},
        {"name": "Secura", "location": "Europe", "players_online": 600},
        {"name": "Nevia", "location": "Europe", "players_online": 400},
        {"name": "Oceanis", "location": "Oceania", "players_online": 20},
        {"name": "Stralis", "location": "Oceania", "players_online": 7}
    ]

    sentinelas = escolher_sentinelas(mundos, {"Europe": 2, "Oceania": 1})

    nomes = [s["mundo"] for s in sentinelas]

    assert nomes == ["Antica", "Secura", "Oceanis"]


    # TESTE : VERIFICAR MUDANÇA #
    # Primeira leitura = None, números iguais = False, números diferentes = True #
def test_verificar_mudanca():

    anterior = {"kills_24h_total": 10, "kills_7d_total": 70}

    assert verificar_mudanca(None, anterior) is None
    assert verificar_mudanca(anterior, {"kills_24h_total": 10, "kills_7d_total": 70}) is False
    assert verificar_mudanca(anterior, {"kills_24h_total": 12, "kills_7d_total": 70}) is True


    # TESTES : FLUXO DA SENTINELA #
    # Usam o banco de testes (banco_teste) e uma API falsa (monkeypatch) #

mundos = [
    {"name": "Antica", "location": "Europe", "players_online": 700},
    {"name": "Secura", "location": "Europe", "players_online": 600},
    {"name": "Nevia", "location": "Europe", "players_online": 400}
]

    # AJUDANTE : DADOS FALSOS DA API #
def dados_falsos(kills):

    return {
        "information": {"timestamp": "2026-11-02T03:30:00Z"},
        "killstatistics": {
            "entries": [{"race": "Yakchal", "last_day_killed": kills, "last_week_killed": kills}]
        }
    }

    # AJUDANTE : HORÁRIO EM BERLIM #
def as_horas(hora):

    return datetime(2026, 11, 2, hora, 5, tzinfo=fuso_tibia)


    # TESTE : CARREGAR SENTINELAS SALVAS #
    # Se todas as sentinelas salvas ainda existem, ficam as mesmas #
def test_carregar_sentinelas_mantem_as_salvas(banco_teste):

    banco.trocar_sentinelas([{"mundo": "Nevia", "regiao": "Europe"}])

    assert sentinela.carregar_sentinelas(mundos) == [{"mundo": "Nevia", "regiao": "Europe"}]

    # TESTE : SENTINELA QUE SUMIU #
    # Se um mundo salvo deixou de existir, escolhe de novo os mais cheios #
def test_carregar_sentinelas_troca_se_mundo_sumiu(banco_teste):

    banco.trocar_sentinelas([{"mundo": "Mundo Extinto", "regiao": "Europe"}])

    nomes = [s["mundo"] for s in sentinela.carregar_sentinelas(mundos)]

    assert nomes == ["Antica", "Secura"]

    # TESTE : VERIFICAR SENTINELAS #
    # 1ª rodada = primeira leitura, 2ª igual = sem mudança, 3ª diferente = atualizou #
    # A última atualização da Europa tem que ser o horário da 3ª rodada #
def test_verificar_sentinelas_detecta_atualizacao(banco_teste, monkeypatch):

    kills = {"valor": 5}
    monkeypatch.setattr(sentinela, "consultar_api", lambda mundo: dados_falsos(kills["valor"]))

    sentinela.verificar_sentinelas(mundos, as_horas(2))
    assert banco.ultima_atualizacao("Europe") is None

    sentinela.verificar_sentinelas(mundos, as_horas(3))
    assert banco.ultima_atualizacao("Europe") is None

    kills["valor"] = 8
    sentinela.verificar_sentinelas(mundos, as_horas(4))
    assert banco.ultima_atualizacao("Europe") == as_horas(4)

    # TESTE : SENTINELA COM API FORA DO AR #
    # Sem resposta da API = não grava leitura e não dá erro #
def test_verificar_sentinelas_api_fora_do_ar(banco_teste, monkeypatch):

    monkeypatch.setattr(sentinela, "consultar_api", lambda mundo: None)

    sentinela.verificar_sentinelas(mundos, as_horas(2))

    assert banco.ultima_leitura("Antica") is None
