print("=======================")
print(" Tibia - Boss Detector")
print("=======================")

import requests 

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
        resposta = requests.get(url)

        if resposta.status_code == 200:
            dados = resposta.json()
            return dados

        else:
            print("Erro ao consultar API")    

    except requests.exceptions.RequestException:
        print("Falha de conexão com a API.")

    # FUNÇÃO : ENCONTRAR CRIATURAS #
def buscar_criaturas(dados, criaturas_raras, data_atividade):

    criaturas_econtradas = []
    
    for criatura in dados["killstatistics"]["entries"]:

        if criatura["race"] in criaturas_raras:

            registro = {
                "data": data_atividade,
                "criatura": criatura["race"],
                "kills": criatura["last_day_killed"]
            }

            criaturas_econtradas.append(registro)

    return criaturas_econtradas

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


    # ESTRUTURA #

from datetime import date, timedelta

hoje = date.today()
ontem = hoje - timedelta(days=1)
print("Hoje é: ", hoje)
print("d-1 é: ", ontem)

mundo = input("Selecione o Mundo: ")

dados = consultar_api(mundo)

registros = []

for nome in criaturas_raras:
    encontrada = False

    for criatura in dados["killstatistics"]["entries"]:

        if criatura["race"] == nome:
            encontrada = True

            registro = {
                "data": ontem,
                "criatura": criatura["race"],
                "kills_24h": criatura["last_day_killed"],
                "kills_7d": criatura["last_week_killed"],
                "encontrada_na_api": True
            }

            registros.append(registro)


    if encontrada == False:
        registro = {
            "data": ontem,
            "criatura": nome,
            "kills_24h": 0,
            "kills_7d": 0,
            "encontrada_na_api": False
        }

        registros.append(registro)


exibir_criaturas(registros)
