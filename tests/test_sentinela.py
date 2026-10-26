from sentinela import escolher_sentinelas, verificar_mudanca


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
