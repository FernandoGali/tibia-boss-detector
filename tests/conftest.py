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


    # FUNÇÃO : SEM BANCO DE TESTES #
    # No computador, o teste é pulado (skip) #
    # No GitHub (CI), o teste falha: lá o banco sempre tem que existir #
def sem_banco_teste(motivo):

    if os.getenv("CI"):
        pytest.fail(motivo)

    pytest.skip(motivo)


    # PREPARAÇÃO : BANCO DE TESTES #
    # Todo teste que pede "banco_teste" roda no banco de testes, vazio #
@pytest.fixture
def banco_teste(monkeypatch):

    url = os.getenv("DATABASE_URL")

    if not url:
        sem_banco_teste("DATABASE_URL não encontrado no .env")

    url_teste = make_conninfo(url, dbname=nome_banco_teste)

    try:
        psycopg.connect(url_teste).close()
    except psycopg.OperationalError:
        sem_banco_teste(f"Banco '{nome_banco_teste}' não existe (veja o README)")

    # A partir daqui, banco.conectar() usa o banco de testes #
    monkeypatch.setenv("DATABASE_URL", url_teste)

    banco.criar_tabelas()
    limpar_banco()

    yield

    limpar_banco()
