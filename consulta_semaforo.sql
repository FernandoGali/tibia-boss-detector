-- CONSULTA : SEMÁFORO --
-- Para um mundo, mostra cada criatura rara com a última aparição naquele mundo, --
-- o intervalo típico (juntando todos os mundos), a próxima aparição prevista e a chance --
-- de aparecer (alta, média ou baixa) --
-- Para testar outro mundo, troque o 'Kalibra' --
-- Na API, o current_date vira a data de Berlim e o 4 vem de banco.minimo_intervalos --

    -- APARIÇÕES : TODOS OS MUNDOS --
    -- Só os dias com morte --
with aparicoes_todas as (
    select mundo, criatura, data_atividade
    from snapshots
    where kills_24h > 0
),

    -- INTERVALOS : DIAS ENTRE DUAS APARIÇÕES SEGUIDAS NO MESMO MUNDO --
    -- O lag pega a aparição anterior da mesma criatura no mesmo mundo --
intervalos as (
    select criatura,
           data_atividade - lag(data_atividade)
               over (partition by mundo, criatura order by data_atividade) as intervalo
    from aparicoes_todas
),

    -- GERAL : INTERVALO TÍPICO DE CADA CRIATURA --
    -- A regra de nascimento é a mesma em todos os mundos, então os intervalos são juntados --
    -- Mediana em vez de média: um nascimento que ninguém matou não estica a previsão --
geral as (
    select criatura,
           count(intervalo) as intervalos,
           percentile_cont(0.5) within group (order by intervalo) as intervalo_tipico
    from intervalos
    group by criatura
),

    -- TOTAIS : EM QUANTAS APARIÇÕES E MUNDOS A PREVISÃO SE BASEIA --
totais as (
    select criatura,
           count(*) as aparicoes_total,
           count(distinct mundo) as mundos_com_aparicao
    from aparicoes_todas
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
       coalesce(t.aparicoes_total, 0) as aparicoes_total,
       coalesce(t.mundos_com_aparicao, 0) as mundos_com_aparicao,
       coalesce(g.intervalos, 0) as intervalos,
       round(g.intervalo_tipico::numeric, 1) as intervalo_tipico,
       m.ultima_aparicao + round(g.intervalo_tipico)::int as proxima_prevista,
       case
           when coalesce(g.intervalos, 0) < 4 then 'Histórico ainda é insuficiente para previsão'
           when m.ultima_aparicao is null then 'Ainda não apareceu neste mundo'
           when current_date - m.ultima_aparicao >= g.intervalo_tipico then 'alta'
           when current_date - m.ultima_aparicao >= g.intervalo_tipico / 2 then 'média'
           else 'baixa'
       end as semaforo
from neste_mundo m
left join geral g using (criatura)
left join totais t using (criatura)
order by m.aparicoes desc, m.criatura;
