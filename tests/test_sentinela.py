from datetime import datetime, timedelta

import banco
import sentinela
from sentinela import escolher_sentinelas, verificar_mudanca
from tempo import fuso_tibia

from ajudantes import dados_falsos


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
    # Usam o banco de testes (conexao) e uma API falsa (monkeypatch) #

mundos = [
    {"name": "Antica", "location": "Europe", "players_online": 700},
    {"name": "Secura", "location": "Europe", "players_online": 600},
    {"name": "Nevia", "location": "Europe", "players_online": 400}
]

    # AJUDANTE : HORÁRIO EM BERLIM #
def as_horas(hora):

    return datetime(2026, 11, 2, hora, 5, tzinfo=fuso_tibia)


    # TESTE : CARREGAR SENTINELAS SALVAS #
    # Se todas as sentinelas salvas ainda existem, ficam as mesmas #
def test_carregar_sentinelas_mantem_as_salvas(conexao):

    banco.trocar_sentinelas(conexao, [{"mundo": "Nevia", "regiao": "Europe"}])

    assert sentinela.carregar_sentinelas(conexao, mundos) == [{"mundo": "Nevia", "regiao": "Europe"}]

    # TESTE : SENTINELA QUE SUMIU #
    # Se um mundo salvo deixou de existir, escolhe de novo os mais cheios #
def test_carregar_sentinelas_troca_se_mundo_sumiu(conexao):

    banco.trocar_sentinelas(conexao, [{"mundo": "Mundo Extinto", "regiao": "Europe"}])

    nomes = [s["mundo"] for s in sentinela.carregar_sentinelas(conexao, mundos)]

    assert nomes == ["Antica", "Secura"]

    # TESTE : VERIFICAR SENTINELAS #
    # 1ª rodada = primeira leitura, 2ª igual = sem mudança, 3ª diferente = atualizou #
    # A última atualização da Europa tem que ser o horário da 3ª rodada #
def test_verificar_sentinelas_detecta_atualizacao(conexao, monkeypatch):

    kills = {"valor": 5}
    monkeypatch.setattr(sentinela, "consultar_api", lambda mundo: dados_falsos(kills["valor"]))

    sentinela.verificar_sentinelas(conexao, mundos, as_horas(2))
    assert banco.ultima_atualizacao(conexao, "Europe") is None

    sentinela.verificar_sentinelas(conexao, mundos, as_horas(3))
    assert banco.ultima_atualizacao(conexao, "Europe") is None

    kills["valor"] = 8
    sentinela.verificar_sentinelas(conexao, mundos, as_horas(4))
    assert banco.ultima_atualizacao(conexao, "Europe") == as_horas(4)

    # TESTE : SENTINELA COM API FORA DO AR #
    # Sem resposta da API = não grava leitura e não dá erro #
def test_verificar_sentinelas_api_fora_do_ar(conexao, monkeypatch):

    monkeypatch.setattr(sentinela, "consultar_api", lambda mundo: None)

    sentinela.verificar_sentinelas(conexao, mundos, as_horas(2))

    assert banco.ultima_leitura(conexao, "Antica") is None


    # TESTE : SENTINELA PARA DEPOIS DE ATUALIZAR #
    # Atualizou às 04:05 de 02/11: até a 01:05 de 03/11 a API nem é consultada #
    # Às 02:05 de 03/11 (hora da virada) volta a consultar #
def test_sentinela_para_depois_de_atualizar(conexao, monkeypatch):

    consultados = []
    kills = {"valor": 5}

    def consultar_falso(mundo):
        consultados.append(mundo)
        return dados_falsos(kills["valor"])

    monkeypatch.setattr(sentinela, "consultar_api", consultar_falso)

    sentinela.verificar_sentinelas(conexao, mundos, as_horas(3))
    kills["valor"] = 8
    sentinela.verificar_sentinelas(conexao, mundos, as_horas(4))

    consultados.clear()
    sentinela.verificar_sentinelas(conexao, mundos, as_horas(5))
    sentinela.verificar_sentinelas(conexao, mundos, as_horas(4) + timedelta(hours=21))

    assert consultados == []

    sentinela.verificar_sentinelas(conexao, mundos, as_horas(4) + timedelta(hours=22))

    assert consultados == ["Antica", "Secura"]

    # TESTE : CADA SENTINELA PARA SOZINHA #
    # A Antica atualizou e a Secura ainda não: só a Secura continua sendo consultada #
def test_sentinela_que_nao_atualizou_continua(conexao, monkeypatch):

    consultados = []
    kills = {"Antica": 5, "Secura": 5}

    def consultar_falso(mundo):
        consultados.append(mundo)
        return dados_falsos(kills[mundo])

    monkeypatch.setattr(sentinela, "consultar_api", consultar_falso)

    sentinela.verificar_sentinelas(conexao, mundos, as_horas(3))
    kills["Antica"] = 8
    sentinela.verificar_sentinelas(conexao, mundos, as_horas(4))

    consultados.clear()
    sentinela.verificar_sentinelas(conexao, mundos, as_horas(5))

    assert consultados == ["Secura"]

    # TESTE : LIMPAR LEITURAS ANTIGAS #
    # Leitura de 31 dias atrás é apagada; a de 29 dias atrás fica #
def test_limpar_leituras_antigas(conexao):

    agora = as_horas(4)

    for dias, mundo in [(31, "Antica"), (29, "Secura")]:
        banco.salvar_leitura(conexao, {
            "mundo": mundo,
            "regiao": "Europe",
            "horario": agora - timedelta(days=dias),
            "timestamp_api": None,
            "kills_24h_total": 5,
            "kills_7d_total": 5,
            "mudou": True
        })

    sentinela.limpar_leituras_antigas(conexao, agora)

    assert banco.ultima_leitura(conexao, "Antica") is None
    assert banco.ultima_leitura(conexao, "Secura") is not None
