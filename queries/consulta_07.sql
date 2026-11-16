-- ============================================================================
-- Pergunta 07: Qual é o tempo médio real de entrega (em dias) e a diferença
--              média em relação ao prazo estimado por Região de destino do
--              cliente nos pedidos entregues?
-- ============================================================================
SELECT
    c.regiao_cliente,
    COUNT(*) AS qtd_itens_entregues,
    ROUND(AVG(f.dias_para_entrega), 2) AS media_dias_entrega_real,
    ROUND(AVG(f.dias_atraso_entrega), 2) AS media_diferenca_estimativa_dias,
    SUM(CASE WHEN s.status_pontualidade_entrega = 'Atrasado' THEN 1 ELSE 0 END) AS qtd_itens_atrasados,
    ROUND(
        100.0 * SUM(CASE WHEN s.status_pontualidade_entrega = 'Atrasado' THEN 1 ELSE 0 END) / COUNT(*),
        2
    ) AS taxa_atraso_pct
FROM dw.fato_vendas_itens f
INNER JOIN dw.dim_cliente c ON f.sk_cliente = c.sk_cliente
INNER JOIN dw.dim_status_pedido s ON f.sk_status_pedido = s.sk_status_pedido
WHERE s.status_pedido_original = 'delivered'
  AND f.dias_para_entrega IS NOT NULL
GROUP BY c.regiao_cliente
ORDER BY media_dias_entrega_real DESC;
