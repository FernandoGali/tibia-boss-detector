import requests
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo

from banco import salvar_registros

    # FUSO HORÁRIO DO TIBIA #
    # O server save e a atualização das kill statistics seguem o horário de Berlim #
fuso_tibia = ZoneInfo("Europe/Berlin")

criaturas_raras = [
    "Yeti", "Crustacea Gigantica", "Dire Penguin", "Man In The Cave", "Massacre", "Mr. Punish", "Rotworm Queen", "Smuggler Baron Silvertoe",
    "The Imperor", "The Pale Count", "The Plasmother", "The Welter", "Tyrn", "White Pale", "Yakchal", "Zulazza the Corruptor", "Apprentice Sheng",
    "Munster", "Necropharus", "Dracola", "The Handmaiden", "Zarabustor", "Furyosa", "Draptor", "Arthom the Hunter", "Xenia", "Undead Cavebear",
    "Battlemaster Zunzu", "Midnight Panther"]

    # FUNÇÕES #

    # FUNÇÃO : CONSULTAR API #
def consultar_api(mundo):

    url = f"https://api.tibiadata.com/v4/killstatistics/{mundo}"

    try:
        resposta = requests.get(url, timeout=10)
    except requests.exceptions.RequestException:
        print("Falha de conexão com a API.")
        return None

    if resposta.status_code != 200:
        print("Erro ao consultar API:", resposta.status_code)
        return None

    return resposta.json()

    # FUNÇÃO : CONSULTAR MUNDOS #
    # Busca a lista de mundos normais (sem os de torneio) #
def consultar_mundos():

    url = "https://api.tibiadata.com/v4/worlds"

    try:
        resposta = requests.get(url, timeout=10)
    except requests.exceptions.RequestException:
        print("Falha de conexão com a API.")
        return None

    if resposta.status_code != 200:
        print("Erro ao consultar API:", resposta.status_code)
        return None

    return resposta.json()["worlds"]["regular_worlds"]

    # FUNÇÃO : DATA DE HOJE NO TIBIA #
    # Usa o horário de Berlim e não o do computador #
def data_hoje_tibia():

    return datetime.now(fuso_tibia).date()


    # FUNÇÃO : EXIBIR CRIATURAS #

def exibir_criaturas(criaturas_encontradas):

    if criaturas_encontradas:
        for criatura in criaturas_encontradas:
            print("-----------------------------------")
            print("Data:", criatura["data"])
            print("Criatura:", criatura["criatura"])
            print("Mortes nas últimas 24h:", criatura["kills_24h"])
            print("Mortes nos últimos 7 dias:", criatura["kills_7d"])
            print("-----------------------------------")
    else:
        print("Nenhuma criatura rara encontrada nesse servidor.")

    # FUNÇÃO : CRIAR REGISTROS #
def criar_registros(dados, criaturas_raras, data_atividade, data_coleta, mundo):
    registros = []

    # Momento em que a API gerou os dados #
    timestamp_api = dados.get("information", {}).get("timestamp")

    for nome in criaturas_raras:
        encontrada = False

        for criatura in dados["killstatistics"]["entries"]:

            if criatura["race"] == nome:
                encontrada = True

                registro = {
                    "data": data_atividade,
                    "data_coleta": data_coleta,
                    "mundo": mundo,
                    "criatura": criatura["race"],
                    "kills_24h": criatura["last_day_killed"],
                    "kills_7d": criatura["last_week_killed"],
                    "encontrada_na_api": True,
                    "timestamp_api": timestamp_api
                }

                registros.append(registro)


        if encontrada == False:
            registro = {
                "data": data_atividade,
                "data_coleta":data_coleta,
                "mundo": mundo,
                "criatura": nome,
                "kills_24h": 0,
                "kills_7d": 0,
                "encontrada_na_api": False,
                "timestamp_api": timestamp_api
            }

            registros.append(registro)

    return registros
    

    # ESTRUTURA #

def main():

    print("=======================")
    print(" Tibia - Boss Detector")
    print("=======================")

    hoje = data_hoje_tibia()

    ontem = hoje - timedelta(days=1)
    print("Hoje é (horário de Berlim): ", hoje)
    print("d-1 é: ", ontem)

    mundo = input("Selecione o Mundo: ")

    dados = consultar_api(mundo)

    if dados is None:
        print("Não foi possível coletar os dados de", mundo)
        return

    registros = criar_registros(dados,criaturas_raras,ontem, hoje,mundo)

    # O banco recusa sozinho o mesmo mundo, criatura e dia (regra UNIQUE) #
    novos = salvar_registros(registros)

    if novos == 0:
        print("Snapshot desse mundo já existe para esse dia.")
    else:
        print("Novo snapshot salvo com sucesso:", novos, "registros.")

    exibir_criaturas(registros)

if __name__ == "__main__":
    main()