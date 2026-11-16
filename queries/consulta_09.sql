-- ============================================================================
-- Pergunta 09: Qual é a participação de cada meio de pagamento no valor total
--              transacionado, na quantidade de transações e qual é o número
--              médio de parcelas contratadas?
-- ============================================================================
SELECT
    tp.tipo_pagamento_pt,
    tp.modalidade_cobranca,
    COUNT(*) AS qtd_transacoes_pagamento,
    COUNT(DISTINCT fp.nk_order_id) AS qtd_pedidos,
    ROUND(SUM(fp.valor_pagamento), 2) AS valor_total_pago,
    ROUND(
        100.0 * SUM(fp.valor_pagamento) / SUM(SUM(fp.valor_pagamento)) OVER (),
        2
    ) AS participacao_valor_pct,
    ROUND(AVG(fp.quantidade_parcelas), 2) AS media_parcelas,
    ROUND(AVG(fp.valor_pagamento), 2) AS ticket_medio_transacao
FROM dw.fato_pagamentos_pedido fp
INNER JOIN dw.dim_tipo_pagamento tp ON fp.sk_tipo_pagamento = tp.sk_tipo_pagamento
GROUP BY tp.tipo_pagamento_pt, tp.modalidade_cobranca
ORDER BY valor_total_pago DESC;
