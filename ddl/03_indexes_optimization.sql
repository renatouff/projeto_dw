-- DATA WAREHOUSE OLIST
-- Criação de índices B-Tree nas chaves estrangeiras das tabelas fato,
-- índices de cobertura em dimensões e visão materializada ROLAP
-- para otimização de consultas analíticas (Etapa 5).


-- 1. Índices nas Chaves Estrangeiras e Colunas de Filtro de dw.fato_vendas_itens
CREATE INDEX IF NOT EXISTS idx_fato_itens_sk_tempo_compra
    ON dw.fato_vendas_itens (sk_tempo_compra);

CREATE INDEX IF NOT EXISTS idx_fato_itens_sk_produto
    ON dw.fato_vendas_itens (sk_produto);

CREATE INDEX IF NOT EXISTS idx_fato_itens_sk_cliente
    ON dw.fato_vendas_itens (sk_cliente);

CREATE INDEX IF NOT EXISTS idx_fato_itens_sk_vendedor
    ON dw.fato_vendas_itens (sk_vendedor);

CREATE INDEX IF NOT EXISTS idx_fato_itens_sk_status
    ON dw.fato_vendas_itens (sk_status_pedido);

-- Índice composto (covering index) para consultas logísticas e temporais seletivas
CREATE INDEX IF NOT EXISTS idx_fato_itens_status_tempo_entrega
    ON dw.fato_vendas_itens (sk_status_pedido, sk_tempo_compra)
    INCLUDE (dias_para_entrega, dias_atraso_entrega, valor_frete, nota_avaliacao);

-- 2. Índices nas Chaves Estrangeiras de dw.fato_pagamentos_pedido
CREATE INDEX IF NOT EXISTS idx_fato_pag_sk_tempo_compra
    ON dw.fato_pagamentos_pedido (sk_tempo_compra);

CREATE INDEX IF NOT EXISTS idx_fato_pag_sk_tipo_pagamento
    ON dw.fato_pagamentos_pedido (sk_tipo_pagamento);

CREATE INDEX IF NOT EXISTS idx_fato_pag_sk_cliente
    ON dw.fato_pagamentos_pedido (sk_cliente);

-- 3. Índices em atributos de filtragem e agrupamento das Dimensões
CREATE INDEX IF NOT EXISTS idx_dim_cliente_regiao_uf
    ON dw.dim_cliente (regiao_cliente, uf_cliente);

CREATE INDEX IF NOT EXISTS idx_dim_cliente_unique_id
    ON dw.dim_cliente (customer_unique_id);

CREATE INDEX IF NOT EXISTS idx_dim_produto_categoria_pt
    ON dw.dim_produto (categoria_pt);

CREATE INDEX IF NOT EXISTS idx_dim_tempo_ano_trimestre
    ON dw.dim_tempo (ano, trimestre);

-- 4. Agregação ROLAP Materializada (Aula 03 - pág. 50: Agregações ROLAP em tabelas)
DROP MATERIALIZED VIEW IF EXISTS dw.mv_resumo_trimestral_vendas;
CREATE MATERIALIZED VIEW dw.mv_resumo_trimestral_vendas AS
SELECT
    COALESCE(t.ano::TEXT, 'TOTAL GERAL') AS ano,
    t.trimestre AS num_trimestre,
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

CREATE INDEX IF NOT EXISTS idx_mv_resumo_trimestral_ano
    ON dw.mv_resumo_trimestral_vendas (ano, num_trimestre);

-- 5. Atualização das estatísticas do catálogo para o otimizador de consultas (Query Planner)
ANALYZE dw.dim_tempo;
ANALYZE dw.dim_cliente;
ANALYZE dw.dim_vendedor;
ANALYZE dw.dim_produto;
ANALYZE dw.dim_status_pedido;
ANALYZE dw.dim_tipo_pagamento;
ANALYZE dw.fato_vendas_itens;
ANALYZE dw.fato_pagamentos_pedido;