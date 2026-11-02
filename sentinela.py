from datetime import timedelta

import banco
from registro import registrar
from tempo import data_atividade
from tibia import calcular_resumo, consultar_api

    # QUANTIDADE DE SENTINELAS POR REGIÃO #
    # A Oceania só tem 3 mundos, então fica com 1 sentinela #
sentinelas_por_regiao = {
    "Europe": 2,
    "North America": 2,
    "South America": 2,
    "Oceania": 1
}

    # QUANTO TEMPO GUARDAR AS LEITURAS #
dias_guardar_leituras = 30

    # FUNÇÕES #

    # FUNÇÃO : ESCOLHER SENTINELAS #
    # Pega os mundos mais cheios de cada região #
def escolher_sentinelas(mundos, sentinelas_por_regiao):

    sentinelas = []

    for regiao, quantidade in sentinelas_por_regiao.items():

        mundos_regiao = [m for m in mundos if m["location"] == regiao]
        mundos_regiao.sort(key=lambda m: m["players_online"], reverse=True)

        for mundo in mundos_regiao[:quantidade]:
            sentinelas.append({"mundo": mundo["name"], "regiao": regiao})

    return sentinelas

    # FUNÇÃO : CARREGAR SENTINELAS #
    # As sentinelas ficam fixas no banco, para comparar sempre os mesmos mundos #
    # Só escolhe de novo se algum mundo salvo deixou de existir #
def carregar_sentinelas(conexao, mundos):

    sentinelas = banco.listar_sentinelas(conexao)

    nomes_mundos = [m["name"] for m in mundos]

    todas_existem = all(s["mundo"] in nomes_mundos for s in sentinelas)

    if sentinelas and todas_existem:
        return sentinelas

    sentinelas = escolher_sentinelas(mundos, sentinelas_por_regiao)
    banco.trocar_sentinelas(conexao, sentinelas)

    registrar("Novas sentinelas escolhidas: " + ", ".join(s["mundo"] for s in sentinelas))

    return sentinelas

    # FUNÇÃO : VERIFICAR MUDANÇA #
    # None = primeira leitura desse mundo, sem nada para comparar #
def verificar_mudanca(anterior, resumo):

    if anterior is None:
        return None

    return (
        anterior["kills_24h_total"] != resumo["kills_24h_total"]
        or anterior["kills_7d_total"] != resumo["kills_7d_total"]
    )

    # FUNÇÃO : JÁ ATUALIZOU HOJE #
    # True se a sentinela já viu a atualização do dia; aí não precisa consultar de novo #
    # Volta a consultar às 02:00 de Berlim (hora_virada), quando começa o dia seguinte #
def ja_atualizou_hoje(ultima_mudanca, agora):

    return ultima_mudanca is not None and data_atividade(ultima_mudanca) >= data_atividade(agora)

    # FUNÇÃO : VERIFICAR SENTINELAS #
    # Consulta cada sentinela, compara com a leitura anterior e grava no banco #
    # Cada sentinela para depois de ver a própria atualização do dia #
def verificar_sentinelas(conexao, mundos, agora):

    sentinelas = carregar_sentinelas(conexao, mundos)
    mudancas = banco.ultimas_mudancas(conexao)

    pausadas = [s["mundo"] for s in sentinelas if ja_atualizou_hoje(mudancas.get(s["mundo"]), agora)]

    if pausadas:
        registrar("Sentinelas que já atualizaram hoje: " + ", ".join(pausadas))

    for sentinela in sentinelas:

        mundo = sentinela["mundo"]

        if mundo in pausadas:
            continue

        dados = consultar_api(mundo)

        if dados is None:
            registrar(mundo + " - não foi possível consultar")
            continue

        resumo = calcular_resumo(dados)
        mudou = verificar_mudanca(banco.ultima_leitura(conexao, mundo), resumo)

        banco.salvar_leitura(conexao, {
            "mundo": mundo,
            "regiao": sentinela["regiao"],
            "horario": agora,
            "timestamp_api": dados.get("information", {}).get("timestamp"),
            "kills_24h_total": resumo["kills_24h_total"],
            "kills_7d_total": resumo["kills_7d_total"],
            "mudou": mudou
        })

        if mudou is None:
            situacao = "primeira leitura"
        elif mudou:
            situacao = "ATUALIZOU"
        else:
            situacao = "sem mudança"

        registrar(f"Sentinela {mundo} ({sentinela['regiao']}) - {situacao}")

    # FUNÇÃO : LIMPAR LEITURAS ANTIGAS #
    # Apaga as leituras com mais de 30 dias, para a tabela não crescer sem parar #
def limpar_leituras_antigas(conexao, agora):

    apagadas = banco.apagar_leituras_antigas(conexao, agora - timedelta(days=dias_guardar_leituras))

    if apagadas:
        registrar(f"{apagadas} leituras antigas da sentinela apagadas")
