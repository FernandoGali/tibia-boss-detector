-- CONSULTA : SEMÁFORO --
-- Para um mundo, mostra cada criatura rara com a última aparição, o intervalo típico, --
-- a próxima aparição prevista e a chance de aparecer (alta, média ou baixa) --
-- Tudo é por criatura e por mundo: nada de outra criatura ou de outro mundo entra na conta --
-- Para testar outro mundo, troque o 'Kalibra' (aparece duas vezes) --
-- Na API, o 4 vem de banco.minimo_intervalos --

    -- ÚLTIMO DIA COLETADO DO MUNDO --
    -- Os dias sem aparecer contam até aqui, e não até hoje (a atualização do dia D traz o D-1) --
with ultimo_dia as (
    select max(data_atividade) as dia
    from snapshots
    where mundo = 'Kalibra'
),

    -- INTERVALOS : DIAS ENTRE DUAS APARIÇÕES SEGUIDAS DA CRIATURA NESTE MUNDO --
    -- O lag pega a aparição anterior da mesma criatura --
intervalos as (
    select criatura, mundo,
           data_atividade - lag(data_atividade)
               over (partition by mundo, criatura order by data_atividade) as intervalo
    from snapshots
    where kills_24h > 0
),

    -- TÍPICO : MEDIANA DOS INTERVALOS DE CADA CRIATURA NESTE MUNDO --
    -- Mediana em vez de média: um nascimento que ninguém matou não estica a previsão --
tipico as (
    select criatura,
           count(intervalo) as intervalos,
           percentile_cont(0.5) within group (order by intervalo) as intervalo_tipico
    from intervalos
    where mundo = 'Kalibra'
    group by criatura
),

    -- NESTE MUNDO : APARIÇÕES E ÚLTIMA APARIÇÃO --
neste_mundo as (
    select criatura,
           count(*) filter (where kills_24h > 0) as aparicoes,
           max(data_atividade) filter (where kills_24h > 0) as ultima_aparicao
    from snapshots
    where mundo = 'Kalibra'
    group by criatura
)

    -- RESULTADO : UMA LINHA POR CRIATURA --
    -- Com menos de 4 intervalos não há previsão --
    -- Semáforo: passou o intervalo = alta, passou da metade = média, senão = baixa --
select m.criatura,
       m.aparicoes,
       m.ultima_aparicao,
       u.dia - m.ultima_aparicao as dias_sem_aparecer,
       coalesce(t.intervalos, 0) as intervalos,
       round(t.intervalo_tipico::numeric, 1) as intervalo_tipico,
       m.ultima_aparicao + round(t.intervalo_tipico)::int as proxima_prevista,
       case
           when coalesce(t.intervalos, 0) < 4 then 'Histórico ainda é insuficiente para previsão'
           when u.dia - m.ultima_aparicao >= t.intervalo_tipico then 'alta'
           when u.dia - m.ultima_aparicao >= t.intervalo_tipico / 2 then 'média'
           else 'baixa'
       end as semaforo
from neste_mundo m
left join tipico t using (criatura)
cross join ultimo_dia u
order by m.aparicoes desc, m.criatura;
