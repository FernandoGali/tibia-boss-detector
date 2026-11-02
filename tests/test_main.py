from contextlib import nullcontext

import banco
import main


    # TESTES #
    # O sentinela e o coletor são trocados por funções falsas que só anotam se foram chamadas #
    # O banco é trocado por uma conexão vazia (nullcontext), então não precisa do PostgreSQL #

    # AJUDANTE : PREPARAR MAIN #
def preparar_main(monkeypatch, mundos):

    chamadas = []

    monkeypatch.setattr(banco, "conectar", nullcontext)
    monkeypatch.setattr(main, "consultar_mundos", lambda: mundos)
    monkeypatch.setattr(main, "verificar_sentinelas", lambda conexao, mundos, agora: chamadas.append("sentinela"))
    monkeypatch.setattr(main, "coletar_pendentes", lambda conexao, mundos, agora: chamadas.append("coletor"))
    monkeypatch.setattr(main, "limpar_leituras_antigas", lambda conexao, agora: chamadas.append("limpeza"))

    return chamadas


    # TESTE : ORDEM DA EXECUÇÃO #
    # Primeiro o sentinela, depois o coletor e, no fim, a limpeza das leituras antigas #
def test_main_roda_sentinela_coletor_e_limpeza(monkeypatch):

    chamadas = preparar_main(monkeypatch, [{"name": "Antica", "location": "Europe"}])

    main.main()

    assert chamadas == ["sentinela", "coletor", "limpeza"]

    # TESTE : SEM LISTA DE MUNDOS #
    # Se a API não devolveu os mundos, não roda nada e tenta na próxima hora #
def test_main_sem_mundos_nao_roda_nada(monkeypatch):

    chamadas = preparar_main(monkeypatch, None)

    main.main()

    assert chamadas == []
