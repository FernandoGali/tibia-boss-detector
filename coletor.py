import logging
import time

import banco
from criaturas import criaturas_raras
from registro import registrar
from sentinela import verificar_mudanca
from tempo import data_atividade
from tibia import calcular_resumo, consultar_api

    # PAUSA ENTRE CONSULTAS #
    # Meio segundo entre um mundo e outro, para não sobrecarregar a API #
pausa_entre_consultas = 0.5

    # FUNÇÕES #

    # FUNÇÃO : CRIAR REGISTROS #
    # Um registro para cada criatura rara; a que não veio na API entra com 0 kills #
def criar_registros(dados, criaturas_raras, data_atividade, data_coleta, mundo):

    # Momento em que a API gerou os dados #
    timestamp_api = dados.get("information", {}).get("timestamp")

    # Dicionário nome -> dados da criatura, para achar cada uma sem percorrer a lista toda #
    na_api = {criatura["race"]: criatura for criatura in dados["killstatistics"]["entries"]}

    registros = []

    for nome in criaturas_raras:

        criatura = na_api.get(nome)

        registros.append({
            "data": data_atividade,
            "data_coleta": data_coleta,
            "mundo": mundo,
            "criatura": nome,
            "kills_24h": criatura["last_day_killed"] if criatura else 0,
            "kills_7d": criatura["last_week_killed"] if criatura else 0,
            "encontrada_na_api": criatura is not None,
            "timestamp_api": timestamp_api
        })

    return registros

    # FUNÇÃO : DADOS REPETIDOS #
    # Se o resumo é igual ao da última coleta, o mundo ainda não atualizou #
def dados_repetidos(anterior, resumo):

    return verificar_mudanca(anterior, resumo) is False

    # FUNÇÃO : COLETAR MUNDO #
    # Consulta um mundo e grava, se os dados forem novos #
    # Devolve True se gravou #
def coletar_mundo(conexao, mundo, regiao, dia, agora):

    dados = consultar_api(mundo)

    if dados is None:
        registrar(f"{mundo} - não foi possível consultar, tenta na próxima hora")
        return False

    resumo = calcular_resumo(dados)

    if dados_repetidos(banco.ultima_coleta(conexao, mundo), resumo):
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

    banco.salvar_coleta(conexao, coleta, registros)

    return True

    # FUNÇÃO : COLETAR PENDENTES #
    # Para cada região, coleta os mundos que ainda não têm o dia da última atualização #
def coletar_pendentes(conexao, mundos, agora):

    regioes = sorted({m["location"] for m in mundos})

    for regiao in regioes:

        atualizacao = banco.ultima_atualizacao(conexao, regiao)

        if atualizacao is None:
            registrar(f"{regiao} - o sentinela ainda não detectou nenhuma atualização")
            continue

        dia = data_atividade(atualizacao)
        ja_coletados = banco.mundos_coletados(conexao, dia)

        pendentes = [m["name"] for m in mundos if m["location"] == regiao and m["name"] not in ja_coletados]

        if not pendentes:
            continue

        registrar(f"{regiao} - coletando {len(pendentes)} mundos para o dia {dia}")

        gravados = 0

        for mundo in pendentes:

            # Um erro num mundo não pode parar a coleta dos outros #
            try:
                if coletar_mundo(conexao, mundo, regiao, dia, agora):
                    gravados += 1
            except Exception:
                logging.exception(f"{mundo} - erro ao coletar, tenta na próxima hora")

            time.sleep(pausa_entre_consultas)

        registrar(f"{regiao} - {gravados} de {len(pendentes)} mundos gravados")
