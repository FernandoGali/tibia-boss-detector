import json
from datetime import datetime
from zoneinfo import ZoneInfo

from main import consultar_api, consultar_mundos, fuso_tibia

    # QUANTIDADE DE SENTINELAS POR REGIÃO #
    # A Oceania só tem 3 mundos, então fica com 1 sentinela #
sentinelas_por_regiao = {
    "Europe": 2,
    "North America": 2,
    "South America": 2,
    "Oceania": 1
}

fuso_brasilia = ZoneInfo("America/Sao_Paulo")

arquivo_sentinelas = "sentinelas.json"
arquivo_log = "sentinela_log.json"

    # FUNÇÕES #

    # FUNÇÃO : LER JSON #
    # Lê um arquivo JSON. Se não existir ou estiver quebrado, devolve o valor padrão #
def ler_json(caminho, padrao):

    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)

    except FileNotFoundError:
        return padrao

    except json.JSONDecodeError:
        return padrao

    # FUNÇÃO : SALVAR JSON #
def salvar_json(caminho, conteudo):

    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(conteudo, arquivo, ensure_ascii=False, indent=4)

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
    # As sentinelas ficam fixas no arquivo, para comparar sempre os mesmos mundos #
    # Só escolhe de novo se algum mundo salvo deixou de existir #
def carregar_sentinelas():

    sentinelas = ler_json(arquivo_sentinelas, [])

    mundos = consultar_mundos()

    if mundos is None:
        return sentinelas

    nomes_mundos = [m["name"] for m in mundos]

    todas_existem = all(s["mundo"] in nomes_mundos for s in sentinelas)

    if sentinelas and todas_existem:
        return sentinelas

    sentinelas = escolher_sentinelas(mundos, sentinelas_por_regiao)
    salvar_json(arquivo_sentinelas, sentinelas)

    print("Novas sentinelas escolhidas:", ", ".join(s["mundo"] for s in sentinelas))

    return sentinelas

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

    # FUNÇÃO : ÚLTIMA LEITURA DO MUNDO #
def ultima_leitura(log, mundo):

    for leitura in reversed(log):
        if leitura["mundo"] == mundo:
            return leitura

    return None

    # FUNÇÃO : VERIFICAR MUDANÇA #
    # None = primeira leitura desse mundo, sem nada para comparar #
def verificar_mudanca(anterior, resumo):

    if anterior is None:
        return None

    return (
        anterior["kills_24h_total"] != resumo["kills_24h_total"]
        or anterior["kills_7d_total"] != resumo["kills_7d_total"]
    )


    # ESTRUTURA #

def main():

    print("=======================")
    print(" Tibia - Sentinela")
    print("=======================")

    agora = datetime.now(fuso_tibia)

    print("Horário de Berlim:  ", agora.strftime("%Y-%m-%d %H:%M"))
    print("Horário de Brasília:", agora.astimezone(fuso_brasilia).strftime("%Y-%m-%d %H:%M"))

    sentinelas = carregar_sentinelas()

    if not sentinelas:
        print("Não foi possível definir as sentinelas.")
        return

    log = ler_json(arquivo_log, [])

    for sentinela in sentinelas:

        mundo = sentinela["mundo"]

        dados = consultar_api(mundo)

        if dados is None:
            print(mundo, "- não foi possível consultar")
            continue

        resumo = calcular_resumo(dados)
        mudou = verificar_mudanca(ultima_leitura(log, mundo), resumo)

        leitura = {
            "mundo": mundo,
            "regiao": sentinela["regiao"],
            "horario_berlim": agora.isoformat(timespec="minutes"),
            "horario_brasilia": agora.astimezone(fuso_brasilia).isoformat(timespec="minutes"),
            "timestamp_api": dados.get("information", {}).get("timestamp"),
            "kills_24h_total": resumo["kills_24h_total"],
            "kills_7d_total": resumo["kills_7d_total"],
            "mudou": mudou
        }

        log.append(leitura)

        if mudou is None:
            situacao = "primeira leitura"
        elif mudou:
            situacao = "ATUALIZOU"
        else:
            situacao = "sem mudança"

        print(f"{mundo} ({sentinela['regiao']}) - {situacao}")

    salvar_json(arquivo_log, log)

if __name__ == "__main__":
    main()
