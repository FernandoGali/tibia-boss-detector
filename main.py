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
def buscar_criaturas(dados, criaturas_raras):

    criaturas_econtradas = []
    
    for criatura in dados["killstatistics"]["entries"]:

        if criatura["race"] in criaturas_raras:

            criaturas_econtradas.append(criatura)

    return criaturas_econtradas

    # FUNÇÃO : EXIBIR CRIATURAS #
def exibir_criaturas(criaturas_encontradas):

    if criaturas_encontradas:
        for criatura in criaturas_encontradas:
            print("-----------------------------------")
            print("Criatura:", criatura["race"])
            print("Mortes no último dia:", criatura["last_day_killed"])
            print("Mortes na última semana:", criatura["last_week_killed"])
            print("-----------------------------------")

    else:
        print("Nenhuma criatura rara encontrada nesse servidor.")


    # ESTRUTURA #
mundo = input("Selecione o Mundo: ")

dados = consultar_api(mundo)

if dados is not None:
    criaturas_encontradas = buscar_criaturas(dados, criaturas_raras)

    exibir_criaturas(criaturas_encontradas)