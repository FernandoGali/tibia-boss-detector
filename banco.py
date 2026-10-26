import os

import psycopg
from dotenv import load_dotenv

    # CONFIGURAÇÃO #
    # Lê o DATABASE_URL do arquivo .env (a senha nunca fica no código) #
load_dotenv()

    # TABELAS #
    # snapshots: uma linha por mundo, criatura e dia #
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
def conectar():

    url = os.getenv("DATABASE_URL")

    if not url:
        raise RuntimeError("DATABASE_URL não encontrado. Crie o arquivo .env (veja o README).")

    return psycopg.connect(url)

    # FUNÇÃO : CRIAR TABELAS #
    # Pode rodar quantas vezes quiser: só cria o que ainda não existe #
def criar_tabelas():

    with conectar() as conexao:
        conexao.execute(tabelas)

    # FUNÇÃO : SALVAR REGISTROS #
    # Grava os registros de um snapshot e devolve quantos eram novos #
    # Se o dia daquele mundo já existe, o banco ignora (ON CONFLICT DO NOTHING) #
def salvar_registros(registros):

    comando = """
        INSERT INTO snapshots (
            mundo, criatura, data_atividade, data_coleta,
            kills_24h, kills_7d, encontrada_na_api, timestamp_api
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (mundo, criatura, data_atividade) DO NOTHING
    """

    novos = 0

    with conectar() as conexao:
        for registro in registros:

            resultado = conexao.execute(comando, (
                registro["mundo"],
                registro["criatura"],
                registro["data"],
                registro["data_coleta"],
                registro["kills_24h"],
                registro["kills_7d"],
                registro["encontrada_na_api"],
                registro["timestamp_api"]
            ))

            novos += resultado.rowcount

    return novos


if __name__ == "__main__":
    criar_tabelas()
    print("Tabelas criadas (ou já existiam).")
