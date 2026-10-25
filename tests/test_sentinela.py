from sentinela import calcular_resumo, escolher_sentinelas, ultima_leitura, verificar_mudanca


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


    # TESTE : ÚLTIMA LEITURA DO MUNDO #
    # Tem que devolver a leitura mais recente daquele mundo, ignorando os outros #
def test_ultima_leitura_pega_a_mais_recente():

    log = [
        {"mundo": "Antica", "kills_24h_total": 1},
        {"mundo": "Secura", "kills_24h_total": 2},
        {"mundo": "Antica", "kills_24h_total": 3}
    ]

    assert ultima_leitura(log, "Antica")["kills_24h_total"] == 3
    assert ultima_leitura(log, "Nevia") is None


    # TESTE : VERIFICAR MUDANÇA #
    # Primeira leitura = None, números iguais = False, números diferentes = True #
def test_verificar_mudanca():

    anterior = {"kills_24h_total": 10, "kills_7d_total": 70}

    assert verificar_mudanca(None, anterior) is None
    assert verificar_mudanca(anterior, {"kills_24h_total": 10, "kills_7d_total": 70}) is False
    assert verificar_mudanca(anterior, {"kills_24h_total": 12, "kills_7d_total": 70}) is True
