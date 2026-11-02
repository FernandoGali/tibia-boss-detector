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
def limpar_banco(conexao):

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


    # PREPARAÇÃO : CONEXÃO COM O BANCO DE TESTES #
    # Todo teste que pede "conexao" recebe uma conexão com o banco de testes, vazio #
@pytest.fixture
def conexao(monkeypatch):

    url = os.getenv("DATABASE_URL")

    if not url:
        sem_banco_teste("DATABASE_URL não encontrado no .env")

    # A partir daqui, banco.conectar() usa o banco de testes #
    monkeypatch.setenv("DATABASE_URL", make_conninfo(url, dbname=nome_banco_teste))

    try:
        conexao = banco.conectar()
    except psycopg.OperationalError:
        sem_banco_teste(f"Banco '{nome_banco_teste}' não existe (veja o README)")

    with conexao:
        banco.criar_tabelas(conexao)
        limpar_banco(conexao)

        yield conexao

        limpar_banco(conexao)
