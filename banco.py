import os

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
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

    # CONFIGURAÇÃO DAS CONEXÕES #
    # dict_row faz cada linha vir como dicionário: linha["mundo"] em vez de linha[0] #
    # autocommit grava cada comando na hora; quando precisa de "tudo ou nada", #
    # a função abre uma transação (conexao.transaction()) #
opcoes_conexao = {"row_factory": dict_row, "autocommit": True}

    # TAMANHO DO POOL DA API #
    # Poucas conexões abertas: o servidor é pequeno e cada conexão ocupa memória #
pool_minimo = 1
pool_maximo = 4

    # FUNÇÃO : URL DO BANCO #
def url_banco():

    url = os.getenv("DATABASE_URL")

    if not url:
        raise RuntimeError("DATABASE_URL não encontrado. Crie o arquivo .env (veja o README).")

    return url

    # FUNÇÃO : CONECTAR #
    # Uma conexão só, usada do começo ao fim de cada execução do main.py #
def conectar():

    return psycopg.connect(url_banco(), **opcoes_conexao)

    # FUNÇÃO : CRIAR POOL #
    # Para a API: conexões que ficam abertas e são reaproveitadas a cada pedido #
    # O pool só abre quando a API liga (with banco.criar_pool() as pool) #
def criar_pool():

    return ConnectionPool(
        url_banco(),
        min_size=pool_minimo,
        max_size=pool_maximo,
        kwargs=opcoes_conexao,
        open=False
    )

    # FUNÇÃO : CRIAR TABELAS #
    # Pode rodar quantas vezes quiser: só cria o que ainda não existe #
def criar_tabelas(conexao):

    conexao.execute(tabelas)


    # SENTINELA #

    # FUNÇÃO : LISTAR SENTINELAS #
def listar_sentinelas(conexao):

    return conexao.execute("SELECT mundo, regiao FROM sentinelas").fetchall()

    # FUNÇÃO : TROCAR SENTINELAS #
    # Apaga as sentinelas antigas e grava as novas, tudo ou nada #
def trocar_sentinelas(conexao, sentinelas):

    with conexao.transaction():

        conexao.execute("DELETE FROM sentinelas")

        conexao.cursor().executemany(
            "INSERT INTO sentinelas (mundo, regiao) VALUES (%s, %s)",
            [(s["mundo"], s["regiao"]) for s in sentinelas]
        )

    # FUNÇÃO : ÚLTIMA LEITURA DO MUNDO #
def ultima_leitura(conexao, mundo):

    comando = """
        SELECT kills_24h_total, kills_7d_total
        FROM leituras_sentinela
        WHERE mundo = %s
        ORDER BY horario DESC
        LIMIT 1
    """

    return conexao.execute(comando, (mundo,)).fetchone()

    # FUNÇÃO : SALVAR LEITURA #
def salvar_leitura(conexao, leitura):

    comando = """
        INSERT INTO leituras_sentinela (
            mundo, regiao, horario, timestamp_api,
            kills_24h_total, kills_7d_total, mudou
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

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
def ultima_atualizacao(conexao, regiao):

    comando = """
        SELECT MAX(horario) AS horario
        FROM leituras_sentinela
        WHERE regiao = %s AND mudou = TRUE
    """

    return conexao.execute(comando, (regiao,)).fetchone()["horario"]


    # COLETOR #

    # FUNÇÃO : MUNDOS JÁ COLETADOS #
    # Devolve os nomes dos mundos que já têm coleta para aquele dia #
def mundos_coletados(conexao, data_atividade):

    linhas = conexao.execute(
        "SELECT mundo FROM coletas WHERE data_atividade = %s",
        (data_atividade,)
    ).fetchall()

    return {linha["mundo"] for linha in linhas}

    # FUNÇÃO : ÚLTIMA COLETA DO MUNDO #
def ultima_coleta(conexao, mundo):

    comando = """
        SELECT kills_24h_total, kills_7d_total
        FROM coletas
        WHERE mundo = %s
        ORDER BY data_atividade DESC
        LIMIT 1
    """

    return conexao.execute(comando, (mundo,)).fetchone()

    # FUNÇÃO : SALVAR COLETA #
    # Grava o resumo do mundo e as criaturas raras juntos #
    # Se der erro no meio, nada é gravado (tudo ou nada) #
def salvar_coleta(conexao, coleta, registros):

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

    # executemany manda todos os snapshots de uma vez, em vez de um por um #
    with conexao.transaction():

        conexao.execute(comando_coleta, (
            coleta["mundo"],
            coleta["regiao"],
            coleta["data_atividade"],
            coleta["horario"],
            coleta["timestamp_api"],
            coleta["kills_24h_total"],
            coleta["kills_7d_total"]
        ))

        conexao.cursor().executemany(comando_snapshot, [
            (
                registro["mundo"],
                registro["criatura"],
                registro["data"],
                registro["data_coleta"],
                registro["kills_24h"],
                registro["kills_7d"],
                registro["encontrada_na_api"],
                registro["timestamp_api"]
            )
            for registro in registros
        ])


    # SITE #

    # FUNÇÃO : LISTAR MUNDOS #
    # Os mundos que já têm coleta, com a região, em ordem alfabética #
def listar_mundos(conexao):

    comando = """
        SELECT DISTINCT mundo, regiao
        FROM coletas
        ORDER BY mundo
    """

    return conexao.execute(comando).fetchall()

    # FUNÇÃO : CONSULTAR SEMÁFORO #
    # A mesma consulta do consulta_semaforo.sql, agora com o mundo, as criaturas #
    # e a data de hoje vindo de fora (%(nome)s), mais as últimas 3 aparições #
def consultar_semaforo(conexao, mundo, criaturas, hoje):

    comando = """
        WITH resumo AS (
            SELECT criatura,
                   COUNT(*) FILTER (WHERE kills_24h > 0) AS aparicoes,
                   MIN(data_atividade) FILTER (WHERE kills_24h > 0) AS primeira_aparicao,
                   MAX(data_atividade) FILTER (WHERE kills_24h > 0) AS ultima_aparicao,
                   (ARRAY_AGG(data_atividade ORDER BY data_atividade DESC)
                        FILTER (WHERE kills_24h > 0))[1:3] AS ultimas_aparicoes
            FROM snapshots
            WHERE mundo = %(mundo)s
              AND criatura = ANY(%(criaturas)s)
            GROUP BY criatura
        ),
        previsao AS (
            SELECT *,
                   (ultima_aparicao - primeira_aparicao) / NULLIF(aparicoes - 1.0, 0) AS intervalo_medio
            FROM resumo
        )
        SELECT criatura,
               aparicoes,
               ultima_aparicao,
               COALESCE(ultimas_aparicoes, ARRAY[]::date[]) AS ultimas_aparicoes,
               ROUND(intervalo_medio, 1) AS intervalo_medio,
               ultima_aparicao + ROUND(intervalo_medio)::int AS proxima_prevista,
               %(hoje)s - ultima_aparicao AS dias_sem_aparecer,
               CASE
                   WHEN aparicoes < 2 THEN NULL
                   WHEN %(hoje)s - ultima_aparicao >= intervalo_medio THEN 'alta'
                   WHEN %(hoje)s - ultima_aparicao >= intervalo_medio / 2 THEN 'média'
                   ELSE 'baixa'
               END AS semaforo,
               CASE
                   WHEN aparicoes = 0 THEN 'Ainda sem histórico de atividade'
                   WHEN aparicoes = 1 THEN 'Histórico ainda é insuficiente para previsão'
               END AS mensagem
        FROM previsao
        ORDER BY aparicoes DESC, criatura
    """

    parametros = {"mundo": mundo, "criaturas": criaturas, "hoje": hoje}

    return conexao.execute(comando, parametros).fetchall()


if __name__ == "__main__":
    with conectar() as conexao:
        criar_tabelas(conexao)
    print("Tabelas criadas (ou já existiam).")
