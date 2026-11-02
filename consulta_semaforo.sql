-- CONSULTA : SEMÁFORO --
-- Para um mundo, mostra cada criatura rara com a última aparição, o intervalo médio, --
-- a próxima aparição prevista e a chance de aparecer (alta, média ou baixa) --
-- Para testar outro mundo, troque o 'Kalibra' --

    -- RESUMO : APARIÇÕES DE CADA CRIATURA --
    -- O filter conta só os dias com morte, mas mantém as criaturas que nunca apareceram --
with resumo as (
    select criatura,
           count(*) filter (where kills_24h > 0) as aparicoes,
           min(data_atividade) filter (where kills_24h > 0) as primeira_aparicao,
           max(data_atividade) filter (where kills_24h > 0) as ultima_aparicao
    from snapshots
    where mundo = 'Kalibra'
    group by criatura
),

    -- PREVISÃO : INTERVALO MÉDIO ENTRE AS APARIÇÕES --
    -- O nullif evita a divisão por zero quando a criatura tem 0 ou 1 aparição --
previsao as (
    select *,
           (ultima_aparicao - primeira_aparicao) / nullif(aparicoes - 1.0, 0) as intervalo_medio
    from resumo
)

    -- RESULTADO : UMA LINHA POR CRIATURA --
    -- Semáforo: passou o intervalo = alta, passou da metade = média, senão = baixa --
    -- Na API, o current_date vai ser trocado pela data de Berlim --
select criatura,
       aparicoes,
       ultima_aparicao,
       round(intervalo_medio, 1) as intervalo_medio,
       ultima_aparicao + round(intervalo_medio)::int as proxima_prevista,
       case
           when aparicoes = 0 then 'Ainda sem histórico de atividade'
           when aparicoes = 1 then 'Histórico ainda é insuficiente para previsão'
           when current_date - ultima_aparicao >= intervalo_medio then 'alta'
           when current_date - ultima_aparicao >= intervalo_medio / 2 then 'média'
           else 'baixa'
       end as semaforo
from previsao
order by aparicoes desc, criatura;
