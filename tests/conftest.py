import os

import psycopg
import pytest
from psycopg.conninfo import make_conninfo

import banco

    # BANCO DE TESTES #
    # Os testes usam um banco separado, para nunca mexer nos dados reais #
    # Usa o mesmo usuário e senha do .env, só troca o nome do banco #
nome_banco_teste = "boss_detector_teste"


    # FUNÇÃO : LIMPAR BANCO #
    # Apaga todas as linhas das tabelas (TRUNCATE), mas mantém as tabelas #
    # Antes, confere se está mesmo no banco de testes #
def limpar_banco():

    with banco.conectar() as conexao:

        nome_atual = conexao.execute("SELECT current_database() AS nome").fetchone()["nome"]
        assert nome_atual == nome_banco_teste, "Tentou limpar um banco que não é o de testes!"

        conexao.execute("TRUNCATE snapshots, coletas, sentinelas, leituras_sentinela RESTART IDENTITY")


    # PREPARAÇÃO : BANCO DE TESTES #
    # Todo teste que pede "banco_teste" roda no banco de testes, vazio #
    # Se o banco de testes não existir, o teste é pulado (skip) em vez de falhar #
@pytest.fixture
def banco_teste(monkeypatch):

    url = os.getenv("DATABASE_URL")

    if not url:
        pytest.skip("DATABASE_URL não encontrado no .env")

    url_teste = make_conninfo(url, dbname=nome_banco_teste)

    try:
        psycopg.connect(url_teste).close()
    except psycopg.OperationalError:
        pytest.skip(f"Banco '{nome_banco_teste}' não existe (veja o README)")

    # A partir daqui, banco.conectar() usa o banco de testes #
    monkeypatch.setenv("DATABASE_URL", url_teste)

    banco.criar_tabelas()
    limpar_banco()

    yield

    limpar_banco()
