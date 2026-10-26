from coletor import criar_registros, dados_repetidos


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
