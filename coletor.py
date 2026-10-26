import time

import banco
from sentinela import verificar_mudanca
from tibia import calcular_resumo, consultar_api, data_atividade, registrar

criaturas_raras = [
    "Yeti", "Crustacea Gigantica", "Dire Penguin", "Man In The Cave", "Massacre", "Mr. Punish", "Rotworm Queen", "Smuggler Baron Silvertoe",
    "The Imperor", "The Pale Count", "The Plasmother", "The Welter", "Tyrn", "White Pale", "Yakchal", "Zulazza the Corruptor", "Apprentice Sheng",
    "Munster", "Necropharus", "Dracola", "The Handmaiden", "Zarabustor", "Furyosa", "Draptor", "Arthom the Hunter", "Xenia", "Undead Cavebear",
    "Battlemaster Zunzu", "Midnight Panther"]

    # PAUSA ENTRE CONSULTAS #
    # Meio segundo entre um mundo e outro, para não sobrecarregar a API #
pausa_entre_consultas = 0.5

    # FUNÇÕES #

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

    # FUNÇÃO : DADOS REPETIDOS #
    # Se o resumo é igual ao da última coleta, o mundo ainda não atualizou #
def dados_repetidos(anterior, resumo):

    return verificar_mudanca(anterior, resumo) is False

    # FUNÇÃO : COLETAR MUNDO #
    # Consulta um mundo e grava, se os dados forem novos #
    # Devolve True se gravou #
def coletar_mundo(mundo, regiao, dia, agora):

    dados = consultar_api(mundo)

    if dados is None:
        registrar(f"{mundo} - não foi possível consultar, tenta na próxima hora")
        return False

    resumo = calcular_resumo(dados)

    if dados_repetidos(banco.ultima_coleta(mundo), resumo):
        registrar(f"{mundo} - ainda não atualizou, tenta na próxima hora")
        return False

    registros = criar_registros(dados, criaturas_raras, dia, agora.date(), mundo)

    coleta = {
        "mundo": mundo,
        "regiao": regiao,
        "data_atividade": dia,
        "horario": agora,
        "timestamp_api": dados.get("information", {}).get("timestamp"),
        "kills_24h_total": resumo["kills_24h_total"],
        "kills_7d_total": resumo["kills_7d_total"]
    }

    banco.salvar_coleta(coleta, registros)

    return True

    # FUNÇÃO : COLETAR PENDENTES #
    # Para cada região, coleta os mundos que ainda não têm o dia da última atualização #
def coletar_pendentes(mundos, agora):

    regioes = sorted({m["location"] for m in mundos})

    for regiao in regioes:

        atualizacao = banco.ultima_atualizacao(regiao)

        if atualizacao is None:
            registrar(f"{regiao} - o sentinela ainda não detectou nenhuma atualização")
            continue

        dia = data_atividade(atualizacao)
        ja_coletados = banco.mundos_coletados(dia)

        pendentes = [m["name"] for m in mundos if m["location"] == regiao and m["name"] not in ja_coletados]

        if not pendentes:
            continue

        registrar(f"{regiao} - coletando {len(pendentes)} mundos para o dia {dia}")

        gravados = 0

        for mundo in pendentes:
            if coletar_mundo(mundo, regiao, dia, agora):
                gravados += 1

            time.sleep(pausa_entre_consultas)

        registrar(f"{regiao} - {gravados} de {len(pendentes)} mundos gravados")
