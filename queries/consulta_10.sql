-- ============================================================================
-- Pergunta 10: Qual é o impacto da pontualidade logística de entrega
--              (No Prazo, Atrasado, Nao Entregue) sobre a nota média de
--              avaliação dos clientes e o tempo médio de entrega?
-- ============================================================================
SELECT
    s.status_pontualidade_entrega,
    COUNT(DISTINCT f.nk_order_id) AS qtd_pedidos,
    COUNT(f.nota_avaliacao) AS qtd_itens_avaliados,
    ROUND(AVG(f.nota_avaliacao), 2) AS nota_media_avaliacao,
    ROUND(AVG(f.dias_para_entrega), 2) AS media_dias_entrega,
    ROUND(AVG(f.dias_atraso_entrega), 2) AS media_dias_atraso
FROM dw.fato_vendas_itens f
INNER JOIN dw.dim_status_pedido s ON f.sk_status_pedido = s.sk_status_pedido
GROUP BY s.status_pontualidade_entrega
ORDER BY nota_media_avaliacao DESC;
