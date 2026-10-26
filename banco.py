import os

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

    # CONFIGURAÇÃO #
    # Lê o DATABASE_URL do arquivo .env (a senha nunca fica no código) #
load_dotenv()

    # TABELAS #
    # snapshots: uma linha por mundo, criatura e dia #
    # coletas: uma linha por mundo e dia, com o resumo das kills do mundo inteiro #
    # A regra UNIQUE faz o próprio banco recusar o mesmo dia duas vezes #
tabelas = """
CREATE TABLE IF NOT EXISTS snapshots (
    id                SERIAL PRIMARY KEY,
    mundo             TEXT NOT NULL,
    criatura          TEXT NOT NULL,
    data_atividade    DATE NOT NULL,
    data_coleta       DATE NOT NULL,
    kills_24h         INTEGER NOT NULL,
    kills_7d          INTEGER NOT NULL,
    encontrada_na_api BOOLEAN NOT NULL,
    timestamp_api     TIMESTAMPTZ,
    UNIQUE (mundo, criatura, data_atividade)
);

CREATE TABLE IF NOT EXISTS coletas (
    id              SERIAL PRIMARY KEY,
    mundo           TEXT NOT NULL,
    regiao          TEXT NOT NULL,
    data_atividade  DATE NOT NULL,
    horario         TIMESTAMPTZ NOT NULL,
    timestamp_api   TIMESTAMPTZ,
    kills_24h_total BIGINT NOT NULL,
    kills_7d_total  BIGINT NOT NULL,
    UNIQUE (mundo, data_atividade)
);

CREATE TABLE IF NOT EXISTS sentinelas (
    mundo  TEXT PRIMARY KEY,
    regiao TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS leituras_sentinela (
    id              SERIAL PRIMARY KEY,
    mundo           TEXT NOT NULL,
    regiao          TEXT NOT NULL,
    horario         TIMESTAMPTZ NOT NULL,
    timestamp_api   TIMESTAMPTZ,
    kills_24h_total BIGINT NOT NULL,
    kills_7d_total  BIGINT NOT NULL,
    mudou           BOOLEAN
);
"""

    # FUNÇÕES #

    # FUNÇÃO : CONECTAR #
    # dict_row faz cada linha vir como dicionário: linha["mundo"] em vez de linha[0] #
def conectar():

    url = os.getenv("DATABASE_URL")

    if not url:
        raise RuntimeError("DATABASE_URL não encontrado. Crie o arquivo .env (veja o README).")

    return psycopg.connect(url, row_factory=dict_row)

    # FUNÇÃO : CRIAR TABELAS #
    # Pode rodar quantas vezes quiser: só cria o que ainda não existe #
def criar_tabelas():

    with conectar() as conexao:
        conexao.execute(tabelas)


    # SENTINELA #

    # FUNÇÃO : LISTAR SENTINELAS #
def listar_sentinelas():

    with conectar() as conexao:
        return conexao.execute("SELECT mundo, regiao FROM sentinelas").fetchall()

    # FUNÇÃO : TROCAR SENTINELAS #
    # Apaga as sentinelas antigas e grava as novas #
def trocar_sentinelas(sentinelas):

    with conectar() as conexao:
        conexao.execute("DELETE FROM sentinelas")

        for sentinela in sentinelas:
            conexao.execute(
                "INSERT INTO sentinelas (mundo, regiao) VALUES (%s, %s)",
                (sentinela["mundo"], sentinela["regiao"])
            )

    # FUNÇÃO : ÚLTIMA LEITURA DO MUNDO #
def ultima_leitura(mundo):

    comando = """
        SELECT kills_24h_total, kills_7d_total
        FROM leituras_sentinela
        WHERE mundo = %s
        ORDER BY horario DESC
        LIMIT 1
    """

    with conectar() as conexao:
        return conexao.execute(comando, (mundo,)).fetchone()

    # FUNÇÃO : SALVAR LEITURA #
def salvar_leitura(leitura):

    comando = """
        INSERT INTO leituras_sentinela (
            mundo, regiao, horario, timestamp_api,
            kills_24h_total, kills_7d_total, mudou
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    with conectar() as conexao:
        conexao.execute(comando, (
            leitura["mundo"],
            leitura["regiao"],
            leitura["horario"],
            leitura["timestamp_api"],
            leitura["kills_24h_total"],
            leitura["kills_7d_total"],
            leitura["mudou"]
        ))

    # FUNÇÃO : ÚLTIMA ATUALIZAÇÃO DA REGIÃO #
    # Horário da leitura mais recente em que uma sentinela da região mudou #
    # None = o sentinela ainda não viu nenhuma atualização nessa região #
def ultima_atualizacao(regiao):

    comando = """
        SELECT MAX(horario) AS horario
        FROM leituras_sentinela
        WHERE regiao = %s AND mudou = TRUE
    """

    with conectar() as conexao:
        return conexao.execute(comando, (regiao,)).fetchone()["horario"]


    # COLETOR #

    # FUNÇÃO : MUNDOS JÁ COLETADOS #
    # Devolve os nomes dos mundos que já têm coleta para aquele dia #
def mundos_coletados(data_atividade):

    with conectar() as conexao:
        linhas = conexao.execute(
            "SELECT mundo FROM coletas WHERE data_atividade = %s",
            (data_atividade,)
        ).fetchall()

    return {linha["mundo"] for linha in linhas}

    # FUNÇÃO : ÚLTIMA COLETA DO MUNDO #
def ultima_coleta(mundo):

    comando = """
        SELECT kills_24h_total, kills_7d_total
        FROM coletas
        WHERE mundo = %s
        ORDER BY data_atividade DESC
        LIMIT 1
    """

    with conectar() as conexao:
        return conexao.execute(comando, (mundo,)).fetchone()

    # FUNÇÃO : SALVAR COLETA #
    # Grava o resumo do mundo e as criaturas raras juntos #
    # Se der erro no meio, nada é gravado (tudo ou nada) #
def salvar_coleta(coleta, registros):

    comando_coleta = """
        INSERT INTO coletas (
            mundo, regiao, data_atividade, horario, timestamp_api,
            kills_24h_total, kills_7d_total
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (mundo, data_atividade) DO NOTHING
    """

    comando_snapshot = """
        INSERT INTO snapshots (
            mundo, criatura, data_atividade, data_coleta,
            kills_24h, kills_7d, encontrada_na_api, timestamp_api
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (mundo, criatura, data_atividade) DO NOTHING
    """

    with conectar() as conexao:

        conexao.execute(comando_coleta, (
            coleta["mundo"],
            coleta["regiao"],
            coleta["data_atividade"],
            coleta["horario"],
            coleta["timestamp_api"],
            coleta["kills_24h_total"],
            coleta["kills_7d_total"]
        ))

        for registro in registros:
            conexao.execute(comando_snapshot, (
                registro["mundo"],
                registro["criatura"],
                registro["data"],
                registro["data_coleta"],
                registro["kills_24h"],
                registro["kills_7d"],
                registro["encontrada_na_api"],
                registro["timestamp_api"]
            ))


if __name__ == "__main__":
    criar_tabelas()
    print("Tabelas criadas (ou já existiam).")
