def test_importar_main():
    import main

    assert callable(main.consultar_api)





from main import buscar_criaturas

def test_buscar_criaturas():
    dados = {
        "killstatistics": {
            "entries":[
                {
                    "race": "Yeti",
                    "last_day_killed": 2
                },
                {
                    "race": "Dragon",
                    "last_day_killed": 15   
                }
            ]
        }
    }

    criaturas_raras = ["Yeti", "Midnight Panther"]
    data_atividade = "2026-10-14"

    resultado = buscar_criaturas(
        dados,
        criaturas_raras,
        data_atividade
    )

    assert len(resultado) == 1
    assert resultado[0]["criatura"] == "Yeti"
    assert resultado[0]["kills"] == 2




from main import criar_registros


def test_criar_registros_inclui_criaturas_ausentes():
    dados = {
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
        "kalibra"
    )

    assert len(registros) == 2

    yeti = next(r for r in registros if r["criatura"] == "Yeti")
    pantera = next(
        r for r in registros
        if r["criatura"] == "Midnight Panther"
    )

    assert yeti["encontrada_na_api"] is True
    assert yeti["kills_24h"] == 2
    assert yeti["kills_7d"] == 5

    assert pantera["encontrada_na_api"] is False
    assert pantera["kills_24h"] == 0
    assert pantera["kills_7d"] == 0
