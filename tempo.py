from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

    # FUSOS HORÁRIOS #
    # O server save e a atualização das kill statistics seguem o horário de Berlim #
fuso_tibia = ZoneInfo("Europe/Berlin")
fuso_brasilia = ZoneInfo("America/Sao_Paulo")

    # HORA DA VIRADA DO DIA NO TIBIA #
    # As kill statistics atualizam de madrugada em Berlim (observado entre 03:04 e 04:05) #
    # Uma atualização detectada antes dessa hora ainda é a do dia anterior #
    # (acontece se o computador ficou desligado e só detectou depois da meia-noite) #
hora_virada = 2

    # FUNÇÕES #

    # FUNÇÃO : AGORA NO TIBIA #
    # Data e hora de Berlim, e não as do computador #
def agora_tibia():

    return datetime.now(fuso_tibia)

    # FUNÇÃO : DATA DA ATIVIDADE #
    # A atualização da madrugada do dia D traz as mortes do dia D-1 #
def data_atividade(horario_atualizacao):

    horario_berlim = horario_atualizacao.astimezone(fuso_tibia)

    dia_atualizacao = (horario_berlim - timedelta(hours=hora_virada)).date()

    return dia_atualizacao - timedelta(days=1)
