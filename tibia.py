import requests

from registro import registrar

    # FUNÇÕES #

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
