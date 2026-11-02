import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests

    # FUSOS HORÁRIOS #
    # O server save e a atualização das kill statistics seguem o horário de Berlim #
fuso_tibia = ZoneInfo("Europe/Berlin")
fuso_brasilia = ZoneInfo("America/Sao_Paulo")

    # HORA DA VIRADA DO DIA NO TIBIA #
    # As kill statistics atualizam de madrugada em Berlim (observado entre 03:04 e 04:05) #
    # Uma atualização detectada antes dessa hora ainda é a do dia anterior #
    # (acontece se o computador ficou desligado e só detectou depois da meia-noite) #
hora_virada = 2

    # FUNÇÕES #

    # FUNÇÃO : REGISTRAR #
    # Mostra a mensagem na tela e também grava no arquivo de log #
    # Quando roda agendado não tem tela, então o arquivo é o que fica #
def registrar(mensagem):

    print(mensagem)
    logging.info(mensagem)

    # FUNÇÃO : CONSULTAR API #
def consultar_api(mundo):

    url = f"https://api.tibiadata.com/v4/killstatistics/{mundo}"

    try:
        resposta = requests.get(url, timeout=10)
    except requests.exceptions.RequestException:
        registrar("Falha de conexão com a API.")
        return None

    if resposta.status_code != 200:
        registrar(f"Erro ao consultar API: {resposta.status_code}")
        return None

    dados = resposta.json()

    # Mundo recém-lançado ainda não tem kill statistics: a API devolve a lista vazia #
    if not dados.get("killstatistics", {}).get("entries"):
        registrar(f"{mundo} - ainda sem kill statistics")
        return None

    return dados

    # FUNÇÃO : CONSULTAR MUNDOS #
    # Busca a lista de mundos normais (sem os de torneio) #
def consultar_mundos():

    url = "https://api.tibiadata.com/v4/worlds"

    try:
        resposta = requests.get(url, timeout=10)
    except requests.exceptions.RequestException:
        registrar("Falha de conexão com a API.")
        return None

    if resposta.status_code != 200:
        registrar(f"Erro ao consultar API: {resposta.status_code}")
        return None

    return resposta.json()["worlds"]["regular_worlds"]

    # FUNÇÃO : AGORA NO TIBIA #
    # Data e hora de Berlim, e não as do computador #
def agora_tibia():

    return datetime.now(fuso_tibia)

    # FUNÇÃO : CALCULAR RESUMO #
    # Soma as kills de todas as criaturas do mundo #
    # Se a soma mudar, as kill statistics foram atualizadas #
def calcular_resumo(dados):

    entradas = dados["killstatistics"]["entries"]

    resumo = {
        "kills_24h_total": sum(c["last_day_killed"] for c in entradas),
        "kills_7d_total": sum(c["last_week_killed"] for c in entradas)
    }

    return resumo

    # FUNÇÃO : DATA DA ATIVIDADE #
    # A atualização da madrugada do dia D traz as mortes do dia D-1 #
def data_atividade(horario_atualizacao):

    horario_berlim = horario_atualizacao.astimezone(fuso_tibia)

    dia_atualizacao = (horario_berlim - timedelta(hours=hora_virada)).date()

    return dia_atualizacao - timedelta(days=1)
