from datetime import date, datetime

import banco
import coletor
from coletor import criar_registros, dados_repetidos
from tempo import fuso_tibia

from ajudantes import dados_falsos


    # TESTES #

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


    # TESTE : DADOS REPETIDOS #
    # Mundo sem coleta anterior = dados novos #
    # Mesmo resumo da coleta anterior = ainda não atualizou #
    # Resumo diferente = dados novos #
def test_dados_repetidos():

    anterior = {"kills_24h_total": 10, "kills_7d_total": 70}

    assert dados_repetidos(None, anterior) is False
    assert dados_repetidos(anterior, {"kills_24h_total": 10, "kills_7d_total": 70}) is True
    assert dados_repetidos(anterior, {"kills_24h_total": 12, "kills_7d_total": 75}) is False


    # TESTES : FLUXO DO COLETOR #
    # Usam o banco de testes (conexao) e uma API falsa (monkeypatch) #

    # AJUDANTE : PREPARAR COLETA #
    # Sentinela da Europa atualizou às 04:05 de 02/11 (Berlim) = dia de atividade 01/11 #
    # A América do Sul ainda não atualizou #
agora = datetime(2026, 11, 2, 4, 5, tzinfo=fuso_tibia)

mundos = [
    {"name": "Antica", "location": "Europe"},
    {"name": "Kalibra", "location": "Europe"},
    {"name": "Inabra", "location": "South America"}
]

def preparar_coleta(conexao, monkeypatch, consultar_api):

    monkeypatch.setattr(coletor, "consultar_api", consultar_api)
    monkeypatch.setattr(coletor, "pausa_entre_consultas", 0)

    banco.salvar_leitura(conexao, {
        "mundo": "Antica",
        "regiao": "Europe",
        "horario": agora,
        "timestamp_api": None,
        "kills_24h_total": 5,
        "kills_7d_total": 5,
        "mudou": True
    })


    # TESTE : COLETAR PENDENTES #
    # Grava só os mundos da região que atualizou, no dia certo #
def test_coletar_pendentes_grava_regiao_que_atualizou(conexao, monkeypatch):

    preparar_coleta(conexao, monkeypatch, lambda mundo: dados_falsos(5))

    coletor.coletar_pendentes(conexao, mundos, agora)

    assert banco.mundos_coletados(conexao, date(2026, 11, 1)) == {"Antica", "Kalibra"}

    # TESTE : NÃO COLETA DUAS VEZES #
    # Na segunda rodada, os mundos já coletados nem são consultados #
def test_coletar_pendentes_nao_repete(conexao, monkeypatch):

    consultados = []

    def consultar_falso(mundo):
        consultados.append(mundo)
        return dados_falsos(5)

    preparar_coleta(conexao, monkeypatch, consultar_falso)

    coletor.coletar_pendentes(conexao, mundos, agora)
    consultados.clear()
    coletor.coletar_pendentes(conexao, mundos, agora)

    assert consultados == []

    # TESTE : ERRO EM UM MUNDO #
    # Se der erro na Antica, o Kalibra tem que ser gravado mesmo assim #
def test_coletar_pendentes_continua_depois_de_erro(conexao, monkeypatch):

    def consultar_falso(mundo):
        if mundo == "Antica":
            raise ValueError("erro de teste")
        return dados_falsos(5)

    preparar_coleta(conexao, monkeypatch, consultar_falso)

    coletor.coletar_pendentes(conexao, mundos, agora)

    assert banco.mundos_coletados(conexao, date(2026, 11, 1)) == {"Kalibra"}

    # TESTE : MUNDO QUE AINDA NÃO ATUALIZOU #
    # Mesmos números da coleta de ontem = não grava, tenta na próxima hora #
def test_coletar_mundo_ignora_dados_repetidos(conexao, monkeypatch):

    preparar_coleta(conexao, monkeypatch, lambda mundo: dados_falsos(5))

    ontem = {
        "mundo": "Kalibra",
        "regiao": "Europe",
        "data_atividade": date(2026, 10, 31),
        "horario": agora,
        "timestamp_api": None,
        "kills_24h_total": 5,
        "kills_7d_total": 5
    }
    banco.salvar_coleta(conexao, ontem, [])

    gravou = coletor.coletar_mundo(conexao, "Kalibra", "Europe", date(2026, 11, 1), agora)

    assert gravou is False
    assert banco.mundos_coletados(conexao, date(2026, 11, 1)) == set()

    # TESTE : API FORA DO AR #
    # Sem resposta da API = não grava e não dá erro #
def test_coletar_mundo_api_fora_do_ar(conexao, monkeypatch):

    preparar_coleta(conexao, monkeypatch, lambda mundo: None)

    gravou = coletor.coletar_mundo(conexao, "Kalibra", "Europe", date(2026, 11, 1), agora)

    assert gravou is False
