    # AJUDANTES DOS TESTES #
    # Funções usadas por mais de um arquivo de teste #

    # AJUDANTE : DADOS FALSOS DA API #
    # Resposta da API com uma criatura só (Yakchal), com as kills pedidas #
def dados_falsos(kills):

    return {
        "information": {"timestamp": "2026-11-02T03:30:00Z"},
        "killstatistics": {
            "entries": [{"race": "Yakchal", "last_day_killed": kills, "last_week_killed": kills}]
        }
    }
