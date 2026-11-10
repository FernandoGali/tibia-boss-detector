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
def semaforo_de(conexao, criatura, mundo="Kalibra"):

    linhas = banco.consultar_semaforo(conexao, mundo, [criatura])

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
    # Tudo é por criatura e por mundo: nada de outra criatura ou de outro mundo entra na conta #
    # O semáforo só aparece com pelo menos banco.minimo_intervalos (4) intervalos naquele mundo #
    # Os dias sem aparecer contam até o último dia coletado do mundo (o maior dia gravado) #

    # AJUDANTE : A CADA 4 DIAS #
    # Kills nos dias 1, 5, 9, 13 e 17 = 4 intervalos de 4 dias (já atinge o mínimo) #
    # dias_sem_kill estende a coleta até o dia que o teste quiser #
def a_cada_4_dias(conexao, dias_sem_kill=(), mundo="Kalibra", criatura="Munster"):

    gravar_snapshots(conexao, mundo, criatura, [nov(1), nov(5), nov(9), nov(13), nov(17)], dias_sem_kill)

    # TESTE : SEMÁFORO ALTA #
    # Intervalo típico de 2 dias; a coleta vai até o dia 12 e a última morte foi no dia 9 #
    # São 3 dias sem aparecer (mais que o intervalo) = alta; próxima prevista no dia 11 #
def test_semaforo_alta(conexao):

    gravar_snapshots(conexao, "Kalibra", "Munster", [nov(1), nov(3), nov(5), nov(7), nov(9)], [nov(10), nov(11), nov(12)])

    linha = semaforo_de(conexao, "Munster")

    assert linha["aparicoes"] == 5
    assert linha["ultima_aparicao"] == nov(9)
    assert linha["ultimas_aparicoes"] == [nov(9), nov(7), nov(5)]
    assert linha["intervalos"] == 4
    assert linha["minimo_intervalos"] == 4
    assert linha["intervalo_tipico"] == 2
    assert linha["ultimo_dia_coletado"] == nov(12)
    assert linha["dias_sem_aparecer"] == 3
    assert linha["proxima_prevista"] == nov(11)
    assert linha["semaforo"] == "alta"
    assert linha["mensagem"] is None

    # TESTE : SEMÁFORO ALTA NO DIA EXATO #
    # Intervalo de 4 dias e exatamente 4 dias sem aparecer (coleta até o dia 21): já conta como alta #
def test_semaforo_alta_no_dia_previsto(conexao):

    a_cada_4_dias(conexao, [nov(18), nov(19), nov(20), nov(21)])

    linha = semaforo_de(conexao, "Munster")

    assert linha["proxima_prevista"] == nov(21)
    assert linha["semaforo"] == "alta"

    # TESTE : SEMÁFORO MÉDIA #
    # Intervalo de 4 dias e 3 dias sem aparecer (passou da metade) = média #
def test_semaforo_media(conexao):

    a_cada_4_dias(conexao, [nov(18), nov(19), nov(20)])

    assert semaforo_de(conexao, "Munster")["semaforo"] == "média"

    # TESTE : SEMÁFORO BAIXA #
    # Intervalo de 4 dias e só 1 dia sem aparecer = baixa #
def test_semaforo_baixa(conexao):

    a_cada_4_dias(conexao, [nov(18)])

    assert semaforo_de(conexao, "Munster")["semaforo"] == "baixa"

    # TESTE : APARECEU NO ÚLTIMO DIA COLETADO #
    # A última morte é o dia mais recente que existe no banco: 0 dias sem aparecer, e não "dias desde hoje" #
def test_semaforo_conta_ate_o_ultimo_dia_coletado(conexao):

    a_cada_4_dias(conexao)

    linha = semaforo_de(conexao, "Munster")

    assert linha["ultimo_dia_coletado"] == nov(17)
    assert linha["dias_sem_aparecer"] == 0
    assert linha["semaforo"] == "baixa"

    # TESTE : MEDIANA, NÃO MÉDIA #
    # Intervalos de 2, 2, 2 e 20 dias (um nascimento que ninguém matou): mediana 2, média seria 6,5 #
def test_semaforo_usa_a_mediana(conexao):

    gravar_snapshots(conexao, "Kalibra", "Munster", [nov(1), nov(3), nov(5), nov(7), nov(27)])

    linha = semaforo_de(conexao, "Munster")

    assert linha["intervalos"] == 4
    assert linha["intervalo_tipico"] == 2

    # TESTE : ABAIXO DO MÍNIMO #
    # Só 3 intervalos (mínimo é 4): sem intervalo, sem previsão, sem semáforo, com mensagem #
def test_semaforo_abaixo_do_minimo(conexao):

    gravar_snapshots(conexao, "Kalibra", "Munster", [nov(1), nov(3), nov(5), nov(7)], [nov(8)])

    linha = semaforo_de(conexao, "Munster")

    assert linha["aparicoes"] == 4
    assert linha["intervalos"] == 3
    assert linha["dias_sem_aparecer"] == 1
    assert linha["intervalo_tipico"] is None
    assert linha["proxima_prevista"] is None
    assert linha["semaforo"] is None
    assert linha["mensagem"] == "Histórico ainda é insuficiente para previsão"

    # TESTE : OUTRO MUNDO NÃO ENTRA NA CONTA #
    # Antica tem intervalos de sobra, mas Kalibra só tem 1: Kalibra fica sem previsão #
def test_semaforo_nao_usa_outro_mundo(conexao):

    gravar_snapshots(conexao, "Kalibra", "Munster", [nov(1), nov(3)])
    a_cada_4_dias(conexao, mundo="Antica")

    kalibra = semaforo_de(conexao, "Munster", mundo="Kalibra")
    antica = semaforo_de(conexao, "Munster", mundo="Antica")

    assert kalibra["intervalos"] == 1
    assert kalibra["semaforo"] is None
    assert antica["intervalos"] == 4
    assert antica["intervalo_tipico"] == 4

    # TESTE : OUTRA CRIATURA NÃO ENTRA NA CONTA #
    # O Yakchal tem intervalos de sobra em Kalibra, mas o Munster só tem 1: Munster fica sem previsão #
def test_semaforo_nao_usa_outra_criatura(conexao):

    gravar_snapshots(conexao, "Kalibra", "Munster", [nov(1), nov(3)])
    a_cada_4_dias(conexao, criatura="Yakchal")

    munster = semaforo_de(conexao, "Munster")
    yakchal = semaforo_de(conexao, "Yakchal")

    assert munster["intervalos"] == 1
    assert munster["semaforo"] is None
    assert yakchal["intervalos"] == 4

    # TESTE : NUNCA APARECEU #
    # Só dias com 0 kills: lista vazia, nada de intervalo, sem semáforo, com mensagem #
def test_semaforo_nunca_apareceu(conexao):

    gravar_snapshots(conexao, "Kalibra", "Yeti", [], [nov(1), nov(2), nov(3)])

    linha = semaforo_de(conexao, "Yeti")

    assert linha["aparicoes"] == 0
    assert linha["intervalos"] == 0
    assert linha["ultima_aparicao"] is None
    assert linha["dias_sem_aparecer"] is None
    assert linha["ultimas_aparicoes"] == []
    assert linha["semaforo"] is None
    assert linha["mensagem"] == "Histórico ainda é insuficiente para previsão"

    # TESTE : SÓ O MUNDO E AS CRIATURAS PEDIDAS #
    # O Munster de Antica e o Yakchal não podem entrar numa consulta do Munster em Kalibra #
def test_semaforo_filtra_mundo_e_criaturas(conexao):

    gravar_snapshots(conexao, "Kalibra", "Munster", [nov(1), nov(3)])
    gravar_snapshots(conexao, "Antica", "Munster", [nov(5), nov(7)])
    gravar_snapshots(conexao, "Kalibra", "Yakchal", [nov(2), nov(4)])

    linhas = banco.consultar_semaforo(conexao, "Kalibra", ["Munster"])

    assert len(linhas) == 1
    assert linhas[0]["criatura"] == "Munster"
    assert linhas[0]["ultimas_aparicoes"] == [nov(3), nov(1)]
    assert linhas[0]["intervalos"] == 1

    # TESTE : ORDEM DO RESULTADO #
    # Primeiro quem apareceu mais vezes; empate fica em ordem alfabética #
def test_semaforo_ordem(conexao):

    gravar_snapshots(conexao, "Kalibra", "Yeti", [], [nov(1)])
    gravar_snapshots(conexao, "Kalibra", "Yakchal", [nov(1), nov(2), nov(3)])
    gravar_snapshots(conexao, "Kalibra", "Munster", [nov(1)])
    gravar_snapshots(conexao, "Kalibra", "Furyosa", [nov(2)])

    linhas = banco.consultar_semaforo(conexao, "Kalibra", ["Yeti", "Yakchal", "Munster", "Furyosa"])

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
