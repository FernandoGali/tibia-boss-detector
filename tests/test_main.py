import main


    # TESTES #
    # O sentinela e o coletor são trocados por funções falsas que só anotam se foram chamadas #

    # AJUDANTE : PREPARAR MAIN #
def preparar_main(monkeypatch, mundos):

    chamadas = []

    monkeypatch.setattr(main, "consultar_mundos", lambda: mundos)
    monkeypatch.setattr(main, "verificar_sentinelas", lambda mundos, agora: chamadas.append("sentinela"))
    monkeypatch.setattr(main, "coletar_pendentes", lambda mundos, agora: chamadas.append("coletor"))

    return chamadas


    # TESTE : ORDEM DA EXECUÇÃO #
    # Primeiro o sentinela, depois o coletor #
def test_main_roda_sentinela_e_depois_coletor(monkeypatch):

    chamadas = preparar_main(monkeypatch, [{"name": "Antica", "location": "Europe"}])

    main.main()

    assert chamadas == ["sentinela", "coletor"]

    # TESTE : SEM LISTA DE MUNDOS #
    # Se a API não devolveu os mundos, não roda nada e tenta na próxima hora #
def test_main_sem_mundos_nao_roda_nada(monkeypatch):

    chamadas = preparar_main(monkeypatch, None)

    main.main()

    assert chamadas == []
