from datetime import date, datetime

import banco
from tempo import fuso_tibia

    # Todos os testes deste arquivo usam o banco de testes (banco_teste) #


    # AJUDANTES #

    # AJUDANTE : DIA DE NOVEMBRO #
    # nov(5) = 05/11/2026, só para os testes ficarem mais curtos #
def nov(dia):

    return date(2026, 11, dia)

    # AJUDANTE : GRAVAR SNAPSHOTS #
    # Grava uma criatura com kills nos dias_com_kill e 0 kills nos dias_sem_kill #
def gravar_snapshots(mundo, criatura, dias_com_kill, dias_sem_kill=()):

    comando = """
        INSERT INTO snapshots (
            mundo, criatura, data_atividade, data_coleta,
            kills_24h, kills_7d, encontrada_na_api
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    with banco.conectar() as conexao:

        for dia in dias_com_kill:
            conexao.execute(comando, (mundo, criatura, dia, dia, 1, 1, True))

        for dia in dias_sem_kill:
            conexao.execute(comando, (mundo, criatura, dia, dia, 0, 0, False))

    # AJUDANTE : SEMÁFORO DE UMA CRIATURA #
    # Consulta uma criatura só e devolve a linha dela #
def semaforo_de(criatura, hoje, mundo="Kalibra"):

    linhas = banco.consultar_semaforo(mundo, [criatura], hoje)

    assert len(linhas) == 1

    return linhas[0]

    # AJUDANTE : COLETA FALSA #
def coleta_falsa(mundo, regiao, dia, kills_24h_total=10):

    coleta = {
        "mundo": mundo,
        "regiao": regiao,
        "data_atividade": dia,
        "horario": datetime(2026, 11, 2, 4, 5, tzinfo=fuso_tibia),
        "timestamp_api": None,
        "kills_24h_total": kills_24h_total,
        "kills_7d_total": 70
    }

    registros = [{
        "mundo": mundo,
        "criatura": "Yakchal",
        "data": dia,
        "data_coleta": dia,
        "kills_24h": 1,
        "kills_7d": 1,
        "encontrada_na_api": True,
        "timestamp_api": None
    }]

    return coleta, registros


    # TESTES : SEMÁFORO #

    # TESTE : SEMÁFORO ALTA #
    # Munster apareceu nos dias 1, 3 e 5: intervalo de 2 dias, próxima no dia 7 #
    # No dia 10, já faz 5 dias sem aparecer (mais que o intervalo) = alta #
def test_semaforo_alta(banco_teste):

    gravar_snapshots("Kalibra", "Munster", [nov(1), nov(3), nov(5)], [nov(2), nov(4)])

    linha = semaforo_de("Munster", nov(10))

    assert linha["aparicoes"] == 3
    assert linha["ultima_aparicao"] == nov(5)
    assert linha["ultimas_aparicoes"] == [nov(5), nov(3), nov(1)]
    assert linha["intervalo_medio"] == 2
    assert linha["proxima_prevista"] == nov(7)
    assert linha["dias_sem_aparecer"] == 5
    assert linha["semaforo"] == "alta"
    assert linha["mensagem"] is None

    # TESTE : SEMÁFORO ALTA NO DIA EXATO #
    # Intervalo de 4 dias e exatamente 4 dias sem aparecer: já conta como alta #
def test_semaforo_alta_no_dia_previsto(banco_teste):

    gravar_snapshots("Kalibra", "Munster", [nov(1), nov(5)])

    assert semaforo_de("Munster", nov(9))["semaforo"] == "alta"

    # TESTE : SEMÁFORO MÉDIA #
    # Intervalo de 4 dias e 3 dias sem aparecer (passou da metade) = média #
def test_semaforo_media(banco_teste):

    gravar_snapshots("Kalibra", "Munster", [nov(1), nov(5)])

    assert semaforo_de("Munster", nov(8))["semaforo"] == "média"

    # TESTE : SEMÁFORO BAIXA #
    # Intervalo de 8 dias e só 1 dia sem aparecer = baixa #
def test_semaforo_baixa(banco_teste):

    gravar_snapshots("Kalibra", "Munster", [nov(1), nov(9)])

    assert semaforo_de("Munster", nov(10))["semaforo"] == "baixa"

    # TESTE : SÓ AS ÚLTIMAS 3 APARIÇÕES #
    # Apareceu 4 vezes, mas a lista mostra só as 3 mais recentes #
def test_semaforo_mostra_so_as_3_ultimas(banco_teste):

    gravar_snapshots("Kalibra", "Munster", [nov(1), nov(2), nov(3), nov(4)])

    linha = semaforo_de("Munster", nov(10))

    assert linha["aparicoes"] == 4
    assert linha["ultimas_aparicoes"] == [nov(4), nov(3), nov(2)]

    # TESTE : UMA APARIÇÃO SÓ #
    # Com 1 aparição não dá para calcular intervalo: sem semáforo, com mensagem #
def test_semaforo_uma_aparicao(banco_teste):

    gravar_snapshots("Kalibra", "White Pale", [nov(1)], [nov(2), nov(3)])

    linha = semaforo_de("White Pale", nov(10))

    assert linha["aparicoes"] == 1
    assert linha["ultimas_aparicoes"] == [nov(1)]
    assert linha["proxima_prevista"] is None
    assert linha["semaforo"] is None
    assert linha["mensagem"] == "Histórico ainda é insuficiente para previsão"

    # TESTE : NUNCA APARECEU #
    # Só dias com 0 kills: lista vazia, sem semáforo, com mensagem #
def test_semaforo_nunca_apareceu(banco_teste):

    gravar_snapshots("Kalibra", "Yeti", [], [nov(1), nov(2), nov(3)])

    linha = semaforo_de("Yeti", nov(10))

    assert linha["aparicoes"] == 0
    assert linha["ultima_aparicao"] is None
    assert linha["ultimas_aparicoes"] == []
    assert linha["semaforo"] is None
    assert linha["mensagem"] == "Ainda sem histórico de atividade"

    # TESTE : SÓ O MUNDO E AS CRIATURAS PEDIDAS #
    # O Munster de Antica e o Yakchal não podem entrar numa consulta do Munster em Kalibra #
def test_semaforo_filtra_mundo_e_criaturas(banco_teste):

    gravar_snapshots("Kalibra", "Munster", [nov(1), nov(3)])
    gravar_snapshots("Antica", "Munster", [nov(5), nov(7)])
    gravar_snapshots("Kalibra", "Yakchal", [nov(2), nov(4)])

    linhas = banco.consultar_semaforo("Kalibra", ["Munster"], nov(10))

    assert len(linhas) == 1
    assert linhas[0]["criatura"] == "Munster"
    assert linhas[0]["ultimas_aparicoes"] == [nov(3), nov(1)]

    # TESTE : ORDEM DO RESULTADO #
    # Primeiro quem apareceu mais vezes; empate fica em ordem alfabética #
def test_semaforo_ordem(banco_teste):

    gravar_snapshots("Kalibra", "Yeti", [], [nov(1)])
    gravar_snapshots("Kalibra", "Yakchal", [nov(1), nov(2), nov(3)])
    gravar_snapshots("Kalibra", "Munster", [nov(1)])
    gravar_snapshots("Kalibra", "Furyosa", [nov(2)])

    linhas = banco.consultar_semaforo("Kalibra", ["Yeti", "Yakchal", "Munster", "Furyosa"], nov(10))

    assert [l["criatura"] for l in linhas] == ["Yakchal", "Furyosa", "Munster", "Yeti"]


    # TESTES : COLETOR #

    # TESTE : SALVAR COLETA #
    # Depois de salvar, o mundo aparece como coletado naquele dia, e só naquele dia #
def test_salvar_coleta(banco_teste):

    banco.salvar_coleta(*coleta_falsa("Kalibra", "Europe", nov(1)))

    assert banco.mundos_coletados(nov(1)) == {"Kalibra"}
    assert banco.mundos_coletados(nov(2)) == set()

    # TESTE : SALVAR O MESMO DIA DUAS VEZES #
    # A segunda vez é ignorada (ON CONFLICT DO NOTHING), sem erro e sem duplicar #
def test_salvar_coleta_repetida_e_ignorada(banco_teste):

    banco.salvar_coleta(*coleta_falsa("Kalibra", "Europe", nov(1), kills_24h_total=10))
    banco.salvar_coleta(*coleta_falsa("Kalibra", "Europe", nov(1), kills_24h_total=99))

    with banco.conectar() as conexao:
        total_snapshots = conexao.execute("SELECT COUNT(*) AS total FROM snapshots").fetchone()["total"]

    assert total_snapshots == 1
    assert banco.ultima_coleta("Kalibra")["kills_24h_total"] == 10

    # TESTE : ÚLTIMA COLETA #
    # Tem que devolver a do dia mais recente; mundo sem coleta = None #
def test_ultima_coleta(banco_teste):

    banco.salvar_coleta(*coleta_falsa("Kalibra", "Europe", nov(2), kills_24h_total=20))
    banco.salvar_coleta(*coleta_falsa("Kalibra", "Europe", nov(1), kills_24h_total=10))

    assert banco.ultima_coleta("Kalibra")["kills_24h_total"] == 20
    assert banco.ultima_coleta("Antica") is None


    # TESTES : SITE #

    # TESTE : LISTAR MUNDOS #
    # Cada mundo aparece uma vez só, em ordem alfabética, com a região #
def test_listar_mundos(banco_teste):

    banco.salvar_coleta(*coleta_falsa("Kalibra", "Europe", nov(1)))
    banco.salvar_coleta(*coleta_falsa("Kalibra", "Europe", nov(2)))
    banco.salvar_coleta(*coleta_falsa("Antica", "Europe", nov(1)))
    banco.salvar_coleta(*coleta_falsa("Inabra", "South America", nov(1)))

    assert banco.listar_mundos() == [
        {"mundo": "Antica", "regiao": "Europe"},
        {"mundo": "Inabra", "regiao": "South America"},
        {"mundo": "Kalibra", "regiao": "Europe"}
    ]


    # TESTES : SENTINELA #

    # TESTE : TROCAR SENTINELAS #
    # As sentinelas antigas somem e ficam só as novas #
def test_trocar_sentinelas(banco_teste):

    banco.trocar_sentinelas([{"mundo": "Antica", "regiao": "Europe"}])
    banco.trocar_sentinelas([{"mundo": "Secura", "regiao": "Europe"}])

    assert banco.listar_sentinelas() == [{"mundo": "Secura", "regiao": "Europe"}]

    # TESTE : LEITURAS DA SENTINELA #
    # ultima_leitura = a mais recente do mundo #
    # ultima_atualizacao = a mais recente em que mudou, só daquela região #
def test_leituras_sentinela(banco_teste):

    def leitura(mundo, regiao, hora, kills, mudou):
        return {
            "mundo": mundo,
            "regiao": regiao,
            "horario": datetime(2026, 11, 2, hora, 5, tzinfo=fuso_tibia),
            "timestamp_api": None,
            "kills_24h_total": kills,
            "kills_7d_total": 70,
            "mudou": mudou
        }

    banco.salvar_leitura(leitura("Antica", "Europe", 2, 10, None))
    banco.salvar_leitura(leitura("Antica", "Europe", 3, 20, True))
    banco.salvar_leitura(leitura("Antica", "Europe", 4, 20, False))

    assert banco.ultima_leitura("Antica")["kills_24h_total"] == 20
    assert banco.ultima_leitura("Secura") is None

    assert banco.ultima_atualizacao("Europe") == datetime(2026, 11, 2, 3, 5, tzinfo=fuso_tibia)
    assert banco.ultima_atualizacao("Oceania") is None
