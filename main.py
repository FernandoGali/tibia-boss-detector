import logging

import banco
from coletor import coletar_pendentes
from registro import configurar_log, registrar
from sentinela import limpar_leituras_antigas, verificar_sentinelas
from tempo import agora_tibia, fuso_brasilia
from tibia import consultar_mundos


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

    # Uma conexão só com o banco para a execução inteira #
    with banco.conectar() as conexao:
        verificar_sentinelas(conexao, mundos, agora)
        coletar_pendentes(conexao, mundos, agora)
        limpar_leituras_antigas(conexao, agora)

if __name__ == "__main__":

    configurar_log()

    # Se der qualquer erro, ele fica registrado no arquivo em vez de sumir #
    try:
        main()
    except Exception:
        logging.exception("Erro ao rodar o Boss Detector")
        raise
