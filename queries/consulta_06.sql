-- ============================================================================
-- Pergunta 06: Quantos clientes reais (customer_unique_id) realizaram mais de um
--              pedido na plataforma e qual é o valor médio gasto por cliente
--              recorrente em comparação aos clientes de compra única?
-- ============================================================================
WITH gastos_por_cliente AS (
    SELECT
        c.customer_unique_id,
        COUNT(DISTINCT f.nk_order_id) AS qtd_pedidos_cliente,
        SUM(f.quantidade_item) AS qtd_itens_comprados,
        SUM(f.valor_total_item) AS gasto_total_cliente
    FROM dw.fato_vendas_itens f
    INNER JOIN dw.dim_cliente c ON f.sk_cliente = c.sk_cliente
    GROUP BY c.customer_unique_id
)
SELECT
    CASE
        WHEN qtd_pedidos_cliente > 1 THEN 'Cliente Recorrente (2+ pedidos)'
        ELSE 'Cliente Compra Unica (1 pedido)'
    END AS perfil_fidelidade,
    COUNT(*) AS qtd_clientes_unicos,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_clientes,
    SUM(qtd_pedidos_cliente) AS total_pedidos,
    ROUND(SUM(gasto_total_cliente), 2) AS faturamento_total,
    ROUND(AVG(gasto_total_cliente), 2) AS gasto_medio_por_cliente
FROM gastos_por_cliente
GROUP BY
    CASE
        WHEN qtd_pedidos_cliente > 1 THEN 'Cliente Recorrente (2+ pedidos)'
        ELSE 'Cliente Compra Unica (1 pedido)'
    END
ORDER BY qtd_clientes_unicos DESC;
