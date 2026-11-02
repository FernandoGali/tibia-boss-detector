import logging

    # ARQUIVO DE LOG #
    # Tudo o que acontece em cada execução fica registrado aqui, com data e hora #
arquivo_log = "boss_detector.log"

    # FUNÇÕES #

    # FUNÇÃO : CONFIGURAR LOG #
    # Grava as mensagens no arquivo com data e hora em cada linha #
def configurar_log():

    logging.basicConfig(
        filename=arquivo_log,
        encoding="utf-8",
        level=logging.INFO,
        format="%(asctime)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M"
    )

    # FUNÇÃO : REGISTRAR #
    # Mostra a mensagem na tela e também grava no arquivo de log #
    # Quando roda agendado não tem tela, então o arquivo é o que fica #
def registrar(mensagem):

    print(mensagem)
    logging.info(mensagem)
