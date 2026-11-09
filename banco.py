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

-- Só os dias com morte, por criatura e mundo: é o que o semáforo lê de todos os mundos --
CREATE INDEX IF NOT EXISTS snapshots_aparicoes
    ON snapshots (criatura, mundo, data_atividade)
    WHERE kills_24h > 0;
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

    # FUNÇÃO : ÚLTIMAS MUDANÇAS DE CADA MUNDO #
    # Horário em que cada sentinela viu a última atualização, numa consulta só #
    # Devolve um dicionário: {"Antica": horário, "Secura": horário, ...} #
def ultimas_mudancas(conexao):

    comando = """
        SELECT mundo, MAX(horario) AS horario
        FROM leituras_sentinela
        WHERE mudou = TRUE
        GROUP BY mundo
    """

    return {linha["mundo"]: linha["horario"] for linha in conexao.execute(comando).fetchall()}

    # FUNÇÃO : APAGAR LEITURAS ANTIGAS #
    # Só as leituras recentes importam; as antigas só ocupam espaço #
def apagar_leituras_antigas(conexao, limite):

    return conexao.execute("DELETE FROM leituras_sentinela WHERE horario < %s", (limite,)).rowcount

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

    # MÍNIMO DE INTERVALOS PARA PREVER #
    # Abaixo disso o semáforo não aparece: poucos intervalos dão uma previsão que não dá para confiar #
minimo_intervalos = 4

    # FUNÇÃO : CONSULTAR SEMÁFORO #
    # A regra de nascimento de uma criatura é a mesma em todos os mundos, então o intervalo #
    # típico é calculado juntando os intervalos de todos os mundos (muito mais dados) #
    # Intervalo = dias entre duas aparições seguidas da criatura no MESMO mundo #
    # Intervalo típico = mediana desses intervalos (resiste a nascimentos que ninguém matou) #
    # O semáforo de cada mundo compara esse intervalo com os dias sem aparecer NAQUELE mundo #
def consultar_semaforo(conexao, mundo, criaturas, hoje):

    comando = """
        WITH aparicoes_todas AS (
            SELECT mundo, criatura, data_atividade
            FROM snapshots
            WHERE criatura = ANY(%(criaturas)s)
              AND kills_24h > 0
        ),
        intervalos AS (
            SELECT criatura,
                   data_atividade - LAG(data_atividade)
                       OVER (PARTITION BY mundo, criatura ORDER BY data_atividade) AS intervalo
            FROM aparicoes_todas
        ),
        geral AS (
            SELECT criatura,
                   COUNT(intervalo) AS intervalos,
                   PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY intervalo) AS intervalo_tipico
            FROM intervalos
            GROUP BY criatura
        ),
        totais AS (
            SELECT criatura,
                   COUNT(*) AS aparicoes_total,
                   COUNT(DISTINCT mundo) AS mundos_com_aparicao
            FROM aparicoes_todas
            GROUP BY criatura
        ),
        neste_mundo AS (
            SELECT criatura,
                   COUNT(*) FILTER (WHERE kills_24h > 0) AS aparicoes,
                   MAX(data_atividade) FILTER (WHERE kills_24h > 0) AS ultima_aparicao,
                   (ARRAY_AGG(data_atividade ORDER BY data_atividade DESC)
                        FILTER (WHERE kills_24h > 0))[1:3] AS ultimas_aparicoes
            FROM snapshots
            WHERE mundo = %(mundo)s
              AND criatura = ANY(%(criaturas)s)
            GROUP BY criatura
        ),
        previsao AS (
            SELECT m.criatura,
                   m.aparicoes,
                   m.ultima_aparicao,
                   COALESCE(m.ultimas_aparicoes, ARRAY[]::date[]) AS ultimas_aparicoes,
                   COALESCE(t.aparicoes_total, 0) AS aparicoes_total,
                   COALESCE(t.mundos_com_aparicao, 0) AS mundos_com_aparicao,
                   COALESCE(g.intervalos, 0) AS intervalos,
                   g.intervalo_tipico,
                   COALESCE(g.intervalos, 0) >= %(minimo)s AS tem_previsao
            FROM neste_mundo m
            LEFT JOIN geral g USING (criatura)
            LEFT JOIN totais t USING (criatura)
        )
        SELECT criatura,
               aparicoes,
               ultima_aparicao,
               ultimas_aparicoes,
               aparicoes_total,
               mundos_com_aparicao,
               intervalos,
               %(minimo)s AS minimo_intervalos,
               %(hoje)s - ultima_aparicao AS dias_sem_aparecer,
               CASE WHEN tem_previsao THEN ROUND(intervalo_tipico::numeric, 1) END AS intervalo_tipico,
               CASE WHEN tem_previsao THEN ultima_aparicao + ROUND(intervalo_tipico)::int END AS proxima_prevista,
               CASE
                   WHEN NOT tem_previsao OR ultima_aparicao IS NULL THEN NULL
                   WHEN %(hoje)s - ultima_aparicao >= intervalo_tipico THEN 'alta'
                   WHEN %(hoje)s - ultima_aparicao >= intervalo_tipico / 2 THEN 'média'
                   ELSE 'baixa'
               END AS semaforo,
               CASE
                   WHEN NOT tem_previsao THEN 'Histórico ainda é insuficiente para previsão'
                   WHEN ultima_aparicao IS NULL THEN 'Ainda não apareceu neste mundo'
               END AS mensagem
        FROM previsao
        ORDER BY aparicoes DESC, criatura
    """

    parametros = {"mundo": mundo, "criaturas": criaturas, "hoje": hoje, "minimo": minimo_intervalos}

    return conexao.execute(comando, parametros).fetchall()


if __name__ == "__main__":
    with conectar() as conexao:
        criar_tabelas(conexao)
    print("Tabelas criadas (ou já existiam).")
