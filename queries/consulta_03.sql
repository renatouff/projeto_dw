-- ============================================================================
-- Pergunta 03: Como se distribuem a receita de produtos e o gasto com frete por
--              Região e UF de destino do cliente, considerando os subtotais por
--              Região e o total geral (GROUPING SETS)?
-- ============================================================================
SELECT
    COALESCE(c.regiao_cliente, 'TOTAL BRASIL') AS regiao,
    COALESCE(c.uf_cliente, 'Subtotal Regiao') AS uf,
    SUM(f.quantidade_item) AS qtd_itens,
    ROUND(SUM(f.valor_preco), 2) AS receita_produtos,
    ROUND(SUM(f.valor_frete), 2) AS total_frete,
    ROUND(AVG(f.valor_frete), 2) AS frete_medio_item,
    ROUND(100.0 * SUM(f.valor_frete) / NULLIF(SUM(f.valor_total_item), 0), 2) AS pct_frete_sobre_total
FROM dw.fato_vendas_itens f
INNER JOIN dw.dim_cliente c ON f.sk_cliente = c.sk_cliente
GROUP BY GROUPING SETS (
    (c.regiao_cliente, c.uf_cliente),
    (c.regiao_cliente),
    ()
)
ORDER BY receita_produtos DESC;
