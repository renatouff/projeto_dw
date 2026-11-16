-- ============================================================================
-- Pergunta 01: Qual é a evolução anual e trimestral da receita de produtos,
--              do valor total de frete e do faturamento bruto dos itens vendidos,
--              incluindo subtotais por ano e total geral (ROLLUP)?
-- ============================================================================
SELECT
    COALESCE(t.ano::TEXT, 'TOTAL GERAL') AS ano,
    COALESCE(t.nome_trimestre, 'Subtotal Ano') AS trimestre,
    SUM(f.quantidade_item) AS qtd_itens_vendidos,
    ROUND(SUM(f.valor_preco), 2) AS receita_produtos,
    ROUND(SUM(f.valor_frete), 2) AS total_frete,
    ROUND(SUM(f.valor_total_item), 2) AS faturamento_total
FROM dw.fato_vendas_itens f
INNER JOIN dw.dim_tempo t ON f.sk_tempo_compra = t.sk_tempo
GROUP BY ROLLUP (t.ano, t.trimestre, t.nome_trimestre)
HAVING (t.trimestre IS NOT NULL AND t.nome_trimestre IS NOT NULL)
    OR (t.trimestre IS NULL AND t.nome_trimestre IS NULL)
ORDER BY t.ano NULLS LAST, t.trimestre NULLS LAST;
