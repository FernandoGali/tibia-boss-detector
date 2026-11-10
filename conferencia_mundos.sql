-- CONFERÊNCIA : A MESMA CRIATURA EM VÁRIOS MUNDOS --
-- Não entra na conta do site. Serve para conferir se as contas fazem sentido: --
-- se a regra de nascimento de uma criatura é a mesma em todos os mundos, o intervalo típico --
-- dela deveria ser parecido de um mundo para o outro --
-- Só entram os mundos onde a criatura já tem pelo menos 4 intervalos (o mínimo do site) --

    -- INTERVALOS : DIAS ENTRE DUAS APARIÇÕES SEGUIDAS DA CRIATURA NO MESMO MUNDO --
with intervalos as (
    select mundo, criatura,
           data_atividade - lag(data_atividade)
               over (partition by mundo, criatura order by data_atividade) as intervalo
    from snapshots
    where kills_24h > 0
),

    -- POR MUNDO : INTERVALO TÍPICO (MEDIANA) DE CADA CRIATURA EM CADA MUNDO --
por_mundo as (
    select criatura, mundo,
           count(intervalo) as intervalos,
           percentile_cont(0.5) within group (order by intervalo) as tipico
    from intervalos
    group by criatura, mundo
    having count(intervalo) >= 4
)

    -- RESULTADO : UMA LINHA POR CRIATURA --
    -- menor / mediana / maior = os intervalos típicos dos mundos, lado a lado --
    -- Se menor e maior estão perto da mediana, os mundos concordam --
    -- Se estão muito longe, a regra pode não ser a mesma, ou faltam dados --
select criatura,
       count(*) as mundos_com_previsao,
       round(min(tipico)::numeric, 1) as menor,
       round((percentile_cont(0.5) within group (order by tipico))::numeric, 1) as mediana,
       round(max(tipico)::numeric, 1) as maior,
       string_agg(mundo || ': ' || round(tipico::numeric, 1), ', ' order by tipico, mundo) as mundos
from por_mundo
group by criatura
order by mundos_com_previsao desc, criatura;
