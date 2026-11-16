-- DATA WAREHOUSE OLIST
-- Criação do esquema dw (Dimensões, Membros Desconhecidos, População da Dimensão Tempo com Feriados Nacionais e Tabelas Fato)

CREATE SCHEMA IF NOT EXISTS dw;

-- Remover tabelas caso existam (ordem reversa para respeitar FKs)
DROP TABLE IF EXISTS dw.fato_pagamentos_pedido CASCADE;
DROP TABLE IF EXISTS dw.fato_vendas_itens CASCADE;
DROP TABLE IF EXISTS dw.dim_tipo_pagamento CASCADE;
DROP TABLE IF EXISTS dw.dim_status_pedido CASCADE;
DROP TABLE IF EXISTS dw.dim_produto CASCADE;
DROP TABLE IF EXISTS dw.dim_vendedor CASCADE;
DROP TABLE IF EXISTS dw.dim_cliente CASCADE;
DROP TABLE IF EXISTS dw.dim_tempo CASCADE;


-- 1. DIMENSÃO TEMPO (dim_tempo)
CREATE TABLE dw.dim_tempo (
    sk_tempo INTEGER PRIMARY KEY,
    data_completa DATE NOT NULL UNIQUE,
    dia INTEGER NOT NULL,
    dia_semana_num INTEGER NOT NULL,
    dia_semana_nome VARCHAR(25) NOT NULL,
    eh_fim_de_semana VARCHAR(3) NOT NULL,
    mes INTEGER NOT NULL,
    nome_mes VARCHAR(20) NOT NULL,
    ano_mes VARCHAR(7) NOT NULL,
    trimestre INTEGER NOT NULL,
    nome_trimestre VARCHAR(20) NOT NULL,
    ano INTEGER NOT NULL,
    eh_feriado_nacional VARCHAR(3) NOT NULL,
    nome_feriado VARCHAR(60) NOT NULL
);

-- Membro desconhecido da dim_tempo (sk_tempo = -1)
INSERT INTO dw.dim_tempo (
    sk_tempo, data_completa, dia, dia_semana_num, dia_semana_nome,
    eh_fim_de_semana, mes, nome_mes, ano_mes, trimestre, nome_trimestre,
    ano, eh_feriado_nacional, nome_feriado
) VALUES (
    -1, DATE '1900-01-01', 0, 0, 'Desconhecido',
    'Nao', 0, 'Desconhecido', '1900-00', 0, 'Desconhecido',
    1900, 'Nao', 'Data Desconhecida / Nao Informada'
);

-- Geração por script do calendário de 2016-01-01 a 2018-12-31 com feriados nacionais
WITH datas AS (
    SELECT generate_series(TIMESTAMP '2016-01-01', TIMESTAMP '2018-12-31', INTERVAL '1 day')::DATE AS dt
),
feriados_nacionais (data_feriado, desc_feriado) AS (
    VALUES
    -- Feriados Móveis Nacionais 2016
    (DATE '2016-02-09', 'Carnaval'),
    (DATE '2016-03-25', 'Sexta-Feira Santa (Paixao de Cristo)'),
    (DATE '2016-03-27', 'Pascoa'),
    (DATE '2016-05-26', 'Corpus Christi'),
    -- Feriados Móveis Nacionais 2017
    (DATE '2017-02-28', 'Carnaval'),
    (DATE '2017-04-14', 'Sexta-Feira Santa (Paixao de Cristo)'),
    (DATE '2017-04-16', 'Pascoa'),
    (DATE '2017-06-15', 'Corpus Christi'),
    -- Feriados Móveis Nacionais 2018
    (DATE '2018-02-13', 'Carnaval'),
    (DATE '2018-03-30', 'Sexta-Feira Santa (Paixao de Cristo)'),
    (DATE '2018-04-01', 'Pascoa'),
    (DATE '2018-05-31', 'Corpus Christi')
)
INSERT INTO dw.dim_tempo (
    sk_tempo, data_completa, dia, dia_semana_num, dia_semana_nome,
    eh_fim_de_semana, mes, nome_mes, ano_mes, trimestre, nome_trimestre,
    ano, eh_feriado_nacional, nome_feriado
)
SELECT
    TO_CHAR(d.dt, 'YYYYMMDD')::INTEGER AS sk_tempo,
    d.dt AS data_completa,
    EXTRACT(DAY FROM d.dt)::INTEGER AS dia,
    EXTRACT(ISODOW FROM d.dt)::INTEGER AS dia_semana_num,
    CASE EXTRACT(ISODOW FROM d.dt)::INTEGER
        WHEN 1 THEN 'Segunda-feira'
        WHEN 2 THEN 'Terca-feira'
        WHEN 3 THEN 'Quarta-feira'
        WHEN 4 THEN 'Quinta-feira'
        WHEN 5 THEN 'Sexta-feira'
        WHEN 6 THEN 'Sabado'
        WHEN 7 THEN 'Domingo'
    END AS dia_semana_nome,
    CASE WHEN EXTRACT(ISODOW FROM d.dt)::INTEGER IN (6, 7) THEN 'Sim' ELSE 'Nao' END AS eh_fim_de_semana,
    EXTRACT(MONTH FROM d.dt)::INTEGER AS mes,
    CASE EXTRACT(MONTH FROM d.dt)::INTEGER
        WHEN 1 THEN 'Janeiro'
        WHEN 2 THEN 'Fevereiro'
        WHEN 3 THEN 'Marco'
        WHEN 4 THEN 'Abril'
        WHEN 5 THEN 'Maio'
        WHEN 6 THEN 'Junho'
        WHEN 7 THEN 'Julho'
        WHEN 8 THEN 'Agosto'
        WHEN 9 THEN 'Setembro'
        WHEN 10 THEN 'Outubro'
        WHEN 11 THEN 'Novembro'
        WHEN 12 THEN 'Dezembro'
    END AS nome_mes,
    TO_CHAR(d.dt, 'YYYY-MM') AS ano_mes,
    EXTRACT(QUARTER FROM d.dt)::INTEGER AS trimestre,
    EXTRACT(QUARTER FROM d.dt)::INTEGER || 'o Trimestre' AS nome_trimestre,
    EXTRACT(YEAR FROM d.dt)::INTEGER AS ano,
    CASE
        WHEN fm.data_feriado IS NOT NULL THEN 'Sim'
        WHEN TO_CHAR(d.dt, 'MM-DD') IN ('01-01', '04-21', '05-01', '09-07', '10-12', '11-02', '11-15', '12-25') THEN 'Sim'
        ELSE 'Nao'
    END AS eh_feriado_nacional,
     COALESCE(
        fm.desc_feriado,
        CASE TO_CHAR(d.dt, 'MM-DD')
            WHEN '01-01' THEN 'Confraternizacao Universal'
            WHEN '04-21' THEN 'Tiradentes'
            WHEN '05-01' THEN 'Dia do Trabalhador'
            WHEN '09-07' THEN 'Independencia do Brasil'
            WHEN '10-12' THEN 'Nossa Senhora Aparecida'
            WHEN '11-02' THEN 'Finados'
            WHEN '11-15' THEN 'Proclamacao da Republica'
            WHEN '12-25' THEN 'Natal'
            ELSE 'Dia Comum'
        END
    ) AS nome_feriado
FROM datas d
LEFT JOIN feriados_nacionais fm ON d.dt = fm.data_feriado
ORDER BY d.dt;

-- 2. DIMENSÃO CLIENTE (dim_cliente)
CREATE TABLE dw.dim_cliente (
    sk_cliente SERIAL PRIMARY KEY,
    nk_customer_id VARCHAR(50) NOT NULL UNIQUE,
    customer_unique_id VARCHAR(50) NOT NULL,
    cep_prefixo_cliente VARCHAR(10) NOT NULL,
    cidade_cliente VARCHAR(100) NOT NULL,
    uf_cliente VARCHAR(5) NOT NULL,
    regiao_cliente VARCHAR(20) NOT NULL,
    latitude_cliente NUMERIC(15, 10) NOT NULL,
    longitude_cliente NUMERIC(15, 10) NOT NULL
);

INSERT INTO dw.dim_cliente (
    sk_cliente, nk_customer_id, customer_unique_id, cep_prefixo_cliente,
    cidade_cliente, uf_cliente, regiao_cliente, latitude_cliente, longitude_cliente
) VALUES (
    -1, 'DESCONHECIDO', 'DESCONHECIDO', '00000',
    'Desconhecida', 'ND', 'Desconhecida', 0.0, 0.0
);

-- 3. DIMENSÃO VENDEDOR (dim_vendedor)
CREATE TABLE dw.dim_vendedor (
    sk_vendedor SERIAL PRIMARY KEY,
    nk_seller_id VARCHAR(50) NOT NULL UNIQUE,
    cep_prefixo_vendedor VARCHAR(10) NOT NULL,
    cidade_vendedor VARCHAR(100) NOT NULL,
    uf_vendedor VARCHAR(5) NOT NULL,
    regiao_vendedor VARCHAR(20) NOT NULL,
    latitude_vendedor NUMERIC(15, 10) NOT NULL,
    longitude_vendedor NUMERIC(15, 10) NOT NULL
);

INSERT INTO dw.dim_vendedor (
    sk_vendedor, nk_seller_id, cep_prefixo_vendedor,
    cidade_vendedor, uf_vendedor, regiao_vendedor, latitude_vendedor, longitude_vendedor
) VALUES (
    -1, 'DESCONHECIDO', '00000',
    'Desconhecida', 'ND', 'Desconhecida', 0.0, 0.0
);

-- 4. DIMENSÃO PRODUTO (dim_produto)
CREATE TABLE dw.dim_produto (
    sk_produto SERIAL PRIMARY KEY,
    nk_product_id VARCHAR(50) NOT NULL UNIQUE,
    categoria_pt VARCHAR(100) NOT NULL,
    categoria_en VARCHAR(100) NOT NULL,
    peso_gramas NUMERIC(12, 2) NOT NULL,
    comprimento_cm NUMERIC(10, 2) NOT NULL,
    altura_cm NUMERIC(10, 2) NOT NULL,
    largura_cm NUMERIC(10, 2) NOT NULL,
    volume_cm3 NUMERIC(14, 2) NOT NULL,
    qtd_fotos INTEGER NOT NULL
);

INSERT INTO dw.dim_produto (
    sk_produto, nk_product_id, categoria_pt, categoria_en,
    peso_gramas, comprimento_cm, altura_cm, largura_cm, volume_cm3, qtd_fotos
) VALUES (
    -1, 'DESCONHECIDO', 'Nao Informada', 'Uninformed',
    0.0, 0.0, 0.0, 0.0, 0.0, 0
);

-- 5. DIMENSÃO STATUS DO PEDIDO (dim_status_pedido)
CREATE TABLE dw.dim_status_pedido (
    sk_status_pedido SERIAL PRIMARY KEY,
    nk_status_codigo VARCHAR(60) NOT NULL UNIQUE,
    status_pedido_original VARCHAR(30) NOT NULL,
    status_pedido_pt VARCHAR(40) NOT NULL,
    status_pontualidade_entrega VARCHAR(30) NOT NULL
);

INSERT INTO dw.dim_status_pedido (
    sk_status_pedido, nk_status_codigo, status_pedido_original,
    status_pedido_pt, status_pontualidade_entrega
) VALUES (
    -1, 'DESCONHECIDO', 'unknown',
    'Desconhecido', 'Desconhecido'
);

-- 6. DIMENSÃO TIPO DE PAGAMENTO (dim_tipo_pagamento)
CREATE TABLE dw.dim_tipo_pagamento (
    sk_tipo_pagamento SERIAL PRIMARY KEY,
    nk_payment_type VARCHAR(30) NOT NULL UNIQUE,
    tipo_pagamento_original VARCHAR(30) NOT NULL,
    tipo_pagamento_pt VARCHAR(40) NOT NULL,
    modalidade_cobranca VARCHAR(30) NOT NULL
);

INSERT INTO dw.dim_tipo_pagamento (
    sk_tipo_pagamento, nk_payment_type, tipo_pagamento_original,
    tipo_pagamento_pt, modalidade_cobranca
) VALUES (
    -1, 'DESCONHECIDO', 'unknown',
    'Desconhecido', 'Desconhecida'
);

-- 7. TABELA FATO 1: VENDAS DE ITENS E LOGÍSTICA (fato_vendas_itens)
-- Grão: 1 linha por item de pedido (nk_order_id + nk_order_item_id)
CREATE TABLE dw.fato_vendas_itens (
    sk_fato_item SERIAL PRIMARY KEY,
    nk_order_id VARCHAR(50) NOT NULL,
    nk_order_item_id INTEGER NOT NULL,
    sk_tempo_compra INTEGER NOT NULL REFERENCES dw.dim_tempo(sk_tempo),
    sk_tempo_entrega INTEGER NOT NULL REFERENCES dw.dim_tempo(sk_tempo),
    sk_tempo_estimada INTEGER NOT NULL REFERENCES dw.dim_tempo(sk_tempo),
    sk_cliente INTEGER NOT NULL REFERENCES dw.dim_cliente(sk_cliente),
    sk_vendedor INTEGER NOT NULL REFERENCES dw.dim_vendedor(sk_vendedor),
    sk_produto INTEGER NOT NULL REFERENCES dw.dim_produto(sk_produto),
    sk_status_pedido INTEGER NOT NULL REFERENCES dw.dim_status_pedido(sk_status_pedido),
    quantidade_item INTEGER NOT NULL DEFAULT 1,
    valor_preco NUMERIC(12, 2) NOT NULL,
    valor_frete NUMERIC(12, 2) NOT NULL,
    valor_total_item NUMERIC(12, 2) NOT NULL,
    dias_para_entrega INTEGER,
    dias_atraso_entrega INTEGER,
    nota_avaliacao INTEGER,
    CONSTRAINT uq_fato_vendas_itens_grao UNIQUE (nk_order_id, nk_order_item_id)
);

-- 8. TABELA FATO 2: PAGAMENTOS DE PEDIDOS (fato_pagamentos_pedido)
-- Grão: 1 linha por sequencial de pagamento do pedido (nk_order_id + nk_payment_sequential)
CREATE TABLE dw.fato_pagamentos_pedido (
    sk_fato_pagamento SERIAL PRIMARY KEY,
    nk_order_id VARCHAR(50) NOT NULL,
    nk_payment_sequential INTEGER NOT NULL,
    sk_tempo_compra INTEGER NOT NULL REFERENCES dw.dim_tempo(sk_tempo),
    sk_cliente INTEGER NOT NULL REFERENCES dw.dim_cliente(sk_cliente),
    sk_status_pedido INTEGER NOT NULL REFERENCES dw.dim_status_pedido(sk_status_pedido),
    sk_tipo_pagamento INTEGER NOT NULL REFERENCES dw.dim_tipo_pagamento(sk_tipo_pagamento),
    valor_pagamento NUMERIC(12, 2) NOT NULL,
    quantidade_parcelas INTEGER NOT NULL,
    CONSTRAINT uq_fato_pagamentos_grao UNIQUE (nk_order_id, nk_payment_sequential)
);