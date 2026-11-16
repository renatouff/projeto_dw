-- ============================================================================
-- Pergunta 05: Qual é o faturamento total, o volume de itens vendidos e a média
--              de faturamento por dia com vendas em dias úteis, finais de semana
--              e feriados nacionais?
-- ============================================================================
SELECT
    CASE
        WHEN t.eh_feriado_nacional = 'Sim' THEN 'Feriado Nacional'
        WHEN t.eh_fim_de_semana = 'Sim' THEN 'Fim de Semana'
        ELSE 'Dia Util'
    END AS tipo_dia_calendario,
    COUNT(DISTINCT t.sk_tempo) AS qtd_dias_com_vendas,
    COUNT(DISTINCT f.nk_order_id) AS qtd_pedidos,
    SUM(f.quantidade_item) AS qtd_itens_vendidos,
    ROUND(SUM(f.valor_total_item), 2) AS faturamento_total,
    ROUND(SUM(f.valor_total_item) / NULLIF(COUNT(DISTINCT t.sk_tempo), 0), 2) AS media_faturamento_por_dia
FROM dw.fato_vendas_itens f
INNER JOIN dw.dim_tempo t ON f.sk_tempo_compra = t.sk_tempo
GROUP BY
    CASE
        WHEN t.eh_feriado_nacional = 'Sim' THEN 'Feriado Nacional'
        WHEN t.eh_fim_de_semana = 'Sim' THEN 'Fim de Semana'
        ELSE 'Dia Util'
    END
ORDER BY media_faturamento_por_dia DESC;
