print("=======================")
print(" Tibia - Boss Detector")
print("=======================")

import requests 

criaturasRaras = [
    "Yeti", "Crustacea Gigantica", "Dire Penguin", "Man In The Cave", "Massacre", "Mr. Punish", "Rotworm Queen", "Smuggler Baron Silvertoe",
    "The Imperor", "The Pale Count", "The Plasmother", "The Welter", "Tyrn", "White Pale", "Yakchal", "Zulazza the Corruptor", "Apprentice Sheng",
    "Munster", "Necropharus", "Dracola", "The Handmaiden", "Zarabustor", "Furyosa", "Draptor", "Arthom the Hunter", "Xenia", "Undead Cavebear",
    "Battlemaster Zunzu", "Midnight Panther"]

mundo = input("Selecione o Mundo: ")

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

dados = consultar_api(mundo)

if dados is not None:
    
    for criatura in dados["killstatistics"]["entries"]:

        if criatura["race"] in criaturasRaras:

            print("-----------------------------------")
            print("Criatura: ",criatura["race"])
            print("Mortes no último dia: ", criatura["last_day_killed"])
            print("Mortes na última semana: ", criatura["last_week_killed"])
            print("-----------------------------------")
        