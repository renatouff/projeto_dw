-- ============================================================================
-- Pergunta 04: Quais são os 10 vendedores com maior receita acumulada de produtos,
--              quantos itens e pedidos atenderam e qual a sua localização?
-- ============================================================================
SELECT
    v.nk_seller_id AS seller_id,
    v.cidade_vendedor,
    v.uf_vendedor,
    v.regiao_vendedor,
    COUNT(DISTINCT f.nk_order_id) AS qtd_pedidos_atendidos,
    SUM(f.quantidade_item) AS qtd_itens_vendidos,
    ROUND(SUM(f.valor_preco), 2) AS receita_produtos,
    ROUND(AVG(f.valor_preco), 2) AS preco_medio_item
FROM dw.fato_vendas_itens f
INNER JOIN dw.dim_vendedor v ON f.sk_vendedor = v.sk_vendedor
GROUP BY v.nk_seller_id, v.cidade_vendedor, v.uf_vendedor, v.regiao_vendedor
ORDER BY receita_produtos DESC
LIMIT 10;
