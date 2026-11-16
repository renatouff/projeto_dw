-- ============================================================================
-- Pergunta 02: Quais são as 10 categorias de produtos (em português e inglês)
--              com maior receita acumulada de vendas, qual o volume de itens
--              vendidos e o ticket médio por item em cada categoria?
-- ============================================================================
SELECT
    p.categoria_pt,
    p.categoria_en,
    SUM(f.quantidade_item) AS qtd_itens_vendidos,
    COUNT(DISTINCT f.nk_order_id) AS qtd_pedidos,
    ROUND(SUM(f.valor_preco), 2) AS receita_produtos,
    ROUND(AVG(f.valor_preco), 2) AS ticket_medio_item,
    ROUND(SUM(f.valor_total_item), 2) AS faturamento_com_frete
FROM dw.fato_vendas_itens f
INNER JOIN dw.dim_produto p ON f.sk_produto = p.sk_produto
GROUP BY p.categoria_pt, p.categoria_en
ORDER BY receita_produtos DESC
LIMIT 10;
