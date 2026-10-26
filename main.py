import logging

from coletor import coletar_pendentes
from sentinela import verificar_sentinelas
from tibia import agora_tibia, consultar_mundos, fuso_brasilia, registrar

    # ARQUIVO DE LOG #
    # Tudo o que acontece em cada execução fica registrado aqui, com data e hora #
arquivo_log = "boss_detector.log"


    # ESTRUTURA #
    # Roda de hora em hora: primeiro o sentinela, depois o coletor #

def main():

    agora = agora_tibia()

    registrar("----- Berlim " + agora.strftime("%Y-%m-%d %H:%M")
              + " | Brasília " + agora.astimezone(fuso_brasilia).strftime("%Y-%m-%d %H:%M") + " -----")

    mundos = consultar_mundos()

    if mundos is None:
        registrar("Não foi possível buscar a lista de mundos, tenta na próxima hora")
        return

    verificar_sentinelas(mundos, agora)
    coletar_pendentes(mundos, agora)

if __name__ == "__main__":

    # Grava as mensagens no arquivo com data e hora em cada linha #
    logging.basicConfig(
        filename=arquivo_log,
        encoding="utf-8",
        level=logging.INFO,
        format="%(asctime)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M"
    )

    # Se der qualquer erro, ele fica registrado no arquivo em vez de sumir #
    try:
        main()
    except Exception:
        logging.exception("Erro ao rodar o Boss Detector")
        raise
