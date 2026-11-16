-- ============================================================================
-- Pergunta 08: Qual é o percentual trimestral de itens entregues com atraso
--              (entregues após a data estimada) e como se comporta o valor
--              médio de frete nesses períodos?
-- ============================================================================
SELECT
    t.ano,
    t.nome_trimestre,
    COUNT(*) AS total_itens_entregues,
    SUM(CASE WHEN s.status_pontualidade_entrega = 'Atrasado' THEN 1 ELSE 0 END) AS itens_atrasados,
    ROUND(
        100.0 * SUM(CASE WHEN s.status_pontualidade_entrega = 'Atrasado' THEN 1 ELSE 0 END) / COUNT(*),
        2
    ) AS pct_atraso,
    ROUND(AVG(f.dias_para_entrega), 2) AS prazo_medio_dias,
    ROUND(AVG(f.valor_frete), 2) AS frete_medio_item
FROM dw.fato_vendas_itens f
INNER JOIN dw.dim_tempo t ON f.sk_tempo_compra = t.sk_tempo
INNER JOIN dw.dim_status_pedido s ON f.sk_status_pedido = s.sk_status_pedido
WHERE s.status_pedido_original = 'delivered'
  AND f.dias_para_entrega IS NOT NULL
GROUP BY t.ano, t.trimestre, t.nome_trimestre
ORDER BY t.ano, t.trimestre;
