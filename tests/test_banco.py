from datetime import date, datetime

import banco
from tempo import fuso_tibia

    # Todos os testes deste arquivo usam o banco de testes (conexao) #


    # AJUDANTES #

    # AJUDANTE : DIA DE NOVEMBRO #
    # nov(5) = 05/11/2026, só para os testes ficarem mais curtos #
def nov(dia):

    return date(2026, 11, dia)

    # AJUDANTE : GRAVAR SNAPSHOTS #
    # Grava uma criatura com kills nos dias_com_kill e 0 kills nos dias_sem_kill #
def gravar_snapshots(conexao, mundo, criatura, dias_com_kill, dias_sem_kill=()):

    comando = """
        INSERT INTO snapshots (
            mundo, criatura, data_atividade, data_coleta,
            kills_24h, kills_7d, encontrada_na_api
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    for dia in dias_com_kill:
        conexao.execute(comando, (mundo, criatura, dia, dia, 1, 1, True))

    for dia in dias_sem_kill:
        conexao.execute(comando, (mundo, criatura, dia, dia, 0, 0, False))

    # AJUDANTE : SEMÁFORO DE UMA CRIATURA #
    # Consulta uma criatura só e devolve a linha dela #
def semaforo_de(conexao, criatura, hoje, mundo="Kalibra"):

    linhas = banco.consultar_semaforo(conexao, mundo, [criatura], hoje)

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
    # O intervalo típico junta os intervalos de todos os mundos #
    # O semáforo só aparece com pelo menos banco.minimo_intervalos (4) intervalos #

    # AJUDANTE : INTERVALO DE 4 DIAS EM ANTICA #
    # Antica nos dias 1, 5, 9, 13 e 17 = 4 intervalos de 4 dias (já atinge o mínimo) #
def antica_a_cada_4_dias(conexao, criatura="Munster"):

    gravar_snapshots(conexao, "Antica", criatura, [nov(1), nov(5), nov(9), nov(13), nov(17)])

    # TESTE : SEMÁFORO ALTA JUNTANDO OS MUNDOS #
    # Kalibra (1, 3, 5) e Antica (2, 4, 6) têm 2 intervalos de 2 dias cada = 4 intervalos, mediana 2 #
    # Em Kalibra a última foi no dia 5: próxima no dia 7; no dia 10 já são 5 dias = alta #
def test_semaforo_alta_juntando_os_mundos(conexao):

    gravar_snapshots(conexao, "Kalibra", "Munster", [nov(1), nov(3), nov(5)], [nov(2), nov(4)])
    gravar_snapshots(conexao, "Antica", "Munster", [nov(2), nov(4), nov(6)])

    linha = semaforo_de(conexao, "Munster", nov(10))

    assert linha["aparicoes"] == 3
    assert linha["ultima_aparicao"] == nov(5)
    assert linha["ultimas_aparicoes"] == [nov(5), nov(3), nov(1)]
    assert linha["aparicoes_total"] == 6
    assert linha["mundos_com_aparicao"] == 2
    assert linha["intervalos"] == 4
    assert linha["minimo_intervalos"] == 4
    assert linha["intervalo_tipico"] == 2
    assert linha["proxima_prevista"] == nov(7)
    assert linha["dias_sem_aparecer"] == 5
    assert linha["semaforo"] == "alta"
    assert linha["mensagem"] is None

    # TESTE : SEMÁFORO ALTA NO DIA EXATO #
    # Intervalo típico de 4 dias; em Kalibra apareceu só no dia 20 (1 vez, mas o intervalo vem de Antica) #
    # No dia 24 são exatamente 4 dias: já conta como alta #
def test_semaforo_alta_no_dia_previsto(conexao):

    antica_a_cada_4_dias(conexao)
    gravar_snapshots(conexao, "Kalibra", "Munster", [nov(20)])

    linha = semaforo_de(conexao, "Munster", nov(24))

    assert linha["aparicoes"] == 1
    assert linha["proxima_prevista"] == nov(24)
    assert linha["semaforo"] == "alta"

    # TESTE : SEMÁFORO MÉDIA #
    # Intervalo típico de 4 dias e 3 dias sem aparecer em Kalibra (passou da metade) = média #
def test_semaforo_media(conexao):

    antica_a_cada_4_dias(conexao)
    gravar_snapshots(conexao, "Kalibra", "Munster", [nov(20)])

    assert semaforo_de(conexao, "Munster", nov(23))["semaforo"] == "média"

    # TESTE : SEMÁFORO BAIXA #
    # Intervalo típico de 4 dias e só 1 dia sem aparecer em Kalibra = baixa #
def test_semaforo_baixa(conexao):

    antica_a_cada_4_dias(conexao)
    gravar_snapshots(conexao, "Kalibra", "Munster", [nov(20)])

    assert semaforo_de(conexao, "Munster", nov(21))["semaforo"] == "baixa"

    # TESTE : MEDIANA, NÃO MÉDIA #
    # Intervalos de 2, 2, 2 e 20 dias (um nascimento que ninguém matou): mediana 2, média seria 6,5 #
def test_semaforo_usa_a_mediana(conexao):

    gravar_snapshots(conexao, "Kalibra", "Munster", [nov(1), nov(3), nov(5), nov(7), nov(27)])

    linha = semaforo_de(conexao, "Munster", nov(28))

    assert linha["intervalos"] == 4
    assert linha["intervalo_tipico"] == 2

    # TESTE : ABAIXO DO MÍNIMO #
    # Só 3 intervalos (mínimo é 4): sem intervalo, sem previsão, sem semáforo, com mensagem #
def test_semaforo_abaixo_do_minimo(conexao):

    gravar_snapshots(conexao, "Kalibra", "Munster", [nov(1), nov(3), nov(5), nov(7)])

    linha = semaforo_de(conexao, "Munster", nov(10))

    assert linha["aparicoes"] == 4
    assert linha["intervalos"] == 3
    assert linha["intervalo_tipico"] is None
    assert linha["proxima_prevista"] is None
    assert linha["semaforo"] is None
    assert linha["mensagem"] == "Histórico ainda é insuficiente para previsão"

    # TESTE : INTERVALO SÓ DENTRO DO MESMO MUNDO #
    # Kalibra no dia 1 e Antica no dia 2 não formam um intervalo de 1 dia: são mundos diferentes #
def test_semaforo_nao_mistura_mundos_no_intervalo(conexao):

    gravar_snapshots(conexao, "Kalibra", "Munster", [nov(1)])
    gravar_snapshots(conexao, "Antica", "Munster", [nov(2)])

    linha = semaforo_de(conexao, "Munster", nov(10))

    assert linha["aparicoes_total"] == 2
    assert linha["intervalos"] == 0

    # TESTE : NUNCA APARECEU NESTE MUNDO, MAS TEM PREVISÃO #
    # Antica já tem intervalos suficientes, mas Kalibra nunca teve o Munster: #
    # não dá para contar dias sem aparecer, então fica sem semáforo e com mensagem própria #
def test_semaforo_nunca_apareceu_neste_mundo(conexao):

    antica_a_cada_4_dias(conexao)
    gravar_snapshots(conexao, "Kalibra", "Munster", [], [nov(1), nov(2)])

    linha = semaforo_de(conexao, "Munster", nov(20))

    assert linha["aparicoes"] == 0
    assert linha["aparicoes_total"] == 5
    assert linha["intervalo_tipico"] == 4
    assert linha["proxima_prevista"] is None
    assert linha["semaforo"] is None
    assert linha["mensagem"] == "Ainda não apareceu neste mundo"

    # TESTE : SÓ AS ÚLTIMAS 3 APARIÇÕES #
    # Apareceu 4 vezes, mas a lista mostra só as 3 mais recentes #
def test_semaforo_mostra_so_as_3_ultimas(conexao):

    gravar_snapshots(conexao, "Kalibra", "Munster", [nov(1), nov(2), nov(3), nov(4)])

    linha = semaforo_de(conexao, "Munster", nov(10))

    assert linha["aparicoes"] == 4
    assert linha["ultimas_aparicoes"] == [nov(4), nov(3), nov(2)]

    # TESTE : NUNCA APARECEU EM LUGAR NENHUM #
    # Só dias com 0 kills: lista vazia, nada de intervalo, sem semáforo, com mensagem #
def test_semaforo_nunca_apareceu(conexao):

    gravar_snapshots(conexao, "Kalibra", "Yeti", [], [nov(1), nov(2), nov(3)])

    linha = semaforo_de(conexao, "Yeti", nov(10))

    assert linha["aparicoes"] == 0
    assert linha["aparicoes_total"] == 0
    assert linha["mundos_com_aparicao"] == 0
    assert linha["intervalos"] == 0
    assert linha["ultima_aparicao"] is None
    assert linha["ultimas_aparicoes"] == []
    assert linha["semaforo"] is None
    assert linha["mensagem"] == "Histórico ainda é insuficiente para previsão"

    # TESTE : SÓ O MUNDO E AS CRIATURAS PEDIDAS #
    # As datas do card são só de Kalibra; o total soma Antica; o Yakchal não entra em nada #
def test_semaforo_filtra_mundo_e_criaturas(conexao):

    gravar_snapshots(conexao, "Kalibra", "Munster", [nov(1), nov(3)])
    gravar_snapshots(conexao, "Antica", "Munster", [nov(5), nov(7)])
    gravar_snapshots(conexao, "Kalibra", "Yakchal", [nov(2), nov(4)])

    linhas = banco.consultar_semaforo(conexao, "Kalibra", ["Munster"], nov(10))

    assert len(linhas) == 1
    assert linhas[0]["criatura"] == "Munster"
    assert linhas[0]["ultimas_aparicoes"] == [nov(3), nov(1)]
    assert linhas[0]["aparicoes_total"] == 4
    assert linhas[0]["intervalos"] == 2

    # TESTE : ORDEM DO RESULTADO #
    # Primeiro quem apareceu mais vezes; empate fica em ordem alfabética #
def test_semaforo_ordem(conexao):

    gravar_snapshots(conexao, "Kalibra", "Yeti", [], [nov(1)])
    gravar_snapshots(conexao, "Kalibra", "Yakchal", [nov(1), nov(2), nov(3)])
    gravar_snapshots(conexao, "Kalibra", "Munster", [nov(1)])
    gravar_snapshots(conexao, "Kalibra", "Furyosa", [nov(2)])

    linhas = banco.consultar_semaforo(conexao, "Kalibra", ["Yeti", "Yakchal", "Munster", "Furyosa"], nov(10))

    assert [l["criatura"] for l in linhas] == ["Yakchal", "Furyosa", "Munster", "Yeti"]


    # TESTES : COLETOR #

    # TESTE : SALVAR COLETA #
    # Depois de salvar, o mundo aparece como coletado naquele dia, e só naquele dia #
def test_salvar_coleta(conexao):

    banco.salvar_coleta(conexao, *coleta_falsa("Kalibra", "Europe", nov(1)))

    assert banco.mundos_coletados(conexao, nov(1)) == {"Kalibra"}
    assert banco.mundos_coletados(conexao, nov(2)) == set()

    # TESTE : SALVAR O MESMO DIA DUAS VEZES #
    # A segunda vez é ignorada (ON CONFLICT DO NOTHING), sem erro e sem duplicar #
def test_salvar_coleta_repetida_e_ignorada(conexao):

    banco.salvar_coleta(conexao, *coleta_falsa("Kalibra", "Europe", nov(1), kills_24h_total=10))
    banco.salvar_coleta(conexao, *coleta_falsa("Kalibra", "Europe", nov(1), kills_24h_total=99))

    total_snapshots = conexao.execute("SELECT COUNT(*) AS total FROM snapshots").fetchone()["total"]

    assert total_snapshots == 1
    assert banco.ultima_coleta(conexao, "Kalibra")["kills_24h_total"] == 10

    # TESTE : ÚLTIMA COLETA #
    # Tem que devolver a do dia mais recente; mundo sem coleta = None #
def test_ultima_coleta(conexao):

    banco.salvar_coleta(conexao, *coleta_falsa("Kalibra", "Europe", nov(2), kills_24h_total=20))
    banco.salvar_coleta(conexao, *coleta_falsa("Kalibra", "Europe", nov(1), kills_24h_total=10))

    assert banco.ultima_coleta(conexao, "Kalibra")["kills_24h_total"] == 20
    assert banco.ultima_coleta(conexao, "Antica") is None


    # TESTES : SITE #

    # TESTE : LISTAR MUNDOS #
    # Cada mundo aparece uma vez só, em ordem alfabética, com a região #
def test_listar_mundos(conexao):

    banco.salvar_coleta(conexao, *coleta_falsa("Kalibra", "Europe", nov(1)))
    banco.salvar_coleta(conexao, *coleta_falsa("Kalibra", "Europe", nov(2)))
    banco.salvar_coleta(conexao, *coleta_falsa("Antica", "Europe", nov(1)))
    banco.salvar_coleta(conexao, *coleta_falsa("Inabra", "South America", nov(1)))

    assert banco.listar_mundos(conexao) == [
        {"mundo": "Antica", "regiao": "Europe"},
        {"mundo": "Inabra", "regiao": "South America"},
        {"mundo": "Kalibra", "regiao": "Europe"}
    ]


    # TESTES : SENTINELA #

    # TESTE : TROCAR SENTINELAS #
    # As sentinelas antigas somem e ficam só as novas #
def test_trocar_sentinelas(conexao):

    banco.trocar_sentinelas(conexao, [{"mundo": "Antica", "regiao": "Europe"}])
    banco.trocar_sentinelas(conexao, [{"mundo": "Secura", "regiao": "Europe"}])

    assert banco.listar_sentinelas(conexao) == [{"mundo": "Secura", "regiao": "Europe"}]

    # TESTE : LEITURAS DA SENTINELA #
    # ultima_leitura = a mais recente do mundo #
    # ultima_atualizacao = a mais recente em que mudou, só daquela região #
def test_leituras_sentinela(conexao):

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

    banco.salvar_leitura(conexao, leitura("Antica", "Europe", 2, 10, None))
    banco.salvar_leitura(conexao, leitura("Antica", "Europe", 3, 20, True))
    banco.salvar_leitura(conexao, leitura("Antica", "Europe", 4, 20, False))

    assert banco.ultima_leitura(conexao, "Antica")["kills_24h_total"] == 20
    assert banco.ultima_leitura(conexao, "Secura") is None

    assert banco.ultima_atualizacao(conexao, "Europe") == datetime(2026, 11, 2, 3, 5, tzinfo=fuso_tibia)
    assert banco.ultima_atualizacao(conexao, "Oceania") is None
