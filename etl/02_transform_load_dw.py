"""
DATA WAREHOUSE OLIST
Executar a Limpeza, Transformação, Auditoria de Linhas Afetadas e
Carga (Inicial até 31/12/2017 e Incremental pós-31/12/2017) no esquema dw.
"""

import os
import sys
import time
import argparse
import psycopg2


def obter_conexao():
    """Conecta ao banco PostgreSQL local dw_olist."""
    return psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        dbname=os.getenv("PGDATABASE", "dw_olist"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", "postgres")
    )


def auditar_regras_limpeza(conn):
    """Calcula e exibe exatamente quantas linhas cada regra de limpeza/transformação afeta."""
    print("=" * 110)
    print("AUDITORIA DAS REGRAS DE LIMPEZA, TRANSFORMAÇÃO E DEDUPLICAÇÃO (DADOS REAIS)")
    print("=" * 110)

    consultas_auditoria = [
        (
            "R01 - Deduplicação de Geolocalização por prefixo de CEP (linhas excedentes consolidadas)",
            "SELECT COUNT(*) - COUNT(DISTINCT LPAD(TRIM(geolocation_zip_code_prefix), 5, '0')) FROM staging.stg_geolocation;"
        ),
        (
            "R02 - Clientes com customer_id distinto do customer_unique_id (recompras / múltiplos pedidos)",
            "SELECT COUNT(*) - COUNT(DISTINCT customer_unique_id) FROM staging.stg_customers;"
        ),
        (
            "R03 - Padronização de grafia/acentuação/caixa em cidades de Clientes e Vendedores",
            """
            SELECT
                (SELECT COUNT(*) FROM staging.stg_customers WHERE customer_city <> INITCAP(TRIM(TRANSLATE(LOWER(customer_city), 'áàâãäéèêëíìîïóòôõöúùûüçñ''/-', 'aaaaaeeeeiiiiooooouuuucn   '))))
                +
                (SELECT COUNT(*) FROM staging.stg_sellers WHERE seller_city <> INITCAP(TRIM(TRANSLATE(LOWER(seller_city), 'áàâãäéèêëíìîïóòôõöúùûüçñ''/-', 'aaaaaeeeeiiiiooooouuuucn   '))));
            """
        ),
        (
            "R04 - Clientes e Vendedores sem CEP em stg_geolocation (tratados com coordenada média da UF)",
            """
            WITH geo_ceps AS (
                SELECT DISTINCT LPAD(TRIM(geolocation_zip_code_prefix), 5, '0') AS cep FROM staging.stg_geolocation
            )
            SELECT
                (SELECT COUNT(*) FROM staging.stg_customers c LEFT JOIN geo_ceps g ON LPAD(TRIM(c.customer_zip_code_prefix), 5, '0') = g.cep WHERE g.cep IS NULL)
                +
                (SELECT COUNT(*) FROM staging.stg_sellers s LEFT JOIN geo_ceps g ON LPAD(TRIM(s.seller_zip_code_prefix), 5, '0') = g.cep WHERE g.cep IS NULL);
            """
        ),
        (
            "R05 - Produtos sem categoria (NULL/vazio -> 'Nao Informada' / 'Uninformed')",
            "SELECT COUNT(*) FROM staging.stg_products WHERE product_category_name IS NULL OR TRIM(product_category_name) = '';"
        ),
        (
            "R06 - Produtos com categoria sem tradução em stg_category_translation (traduzidos manualmente)",
            """
            SELECT COUNT(*) FROM staging.stg_products p
            LEFT JOIN staging.stg_category_translation t ON TRIM(p.product_category_name) = TRIM(t.product_category_name)
            WHERE p.product_category_name IS NOT NULL AND TRIM(p.product_category_name) <> ''
              AND t.product_category_name_english IS NULL;
            """
        ),
        (
            "R07 - Produtos com peso ou dimensões físicas ausentes (NULL -> 0.0)",
            """
            SELECT COUNT(*) FROM staging.stg_products
            WHERE product_weight_g IS NULL OR product_length_cm IS NULL OR product_height_cm IS NULL OR product_width_cm IS NULL;
            """
        ),
        (
            "R08 - Avaliações com review_id repetido em stg_order_reviews",
            "SELECT COUNT(*) - COUNT(DISTINCT review_id) FROM staging.stg_order_reviews;"
        ),
        (
            "R09 - Avaliações excedentes por pedido (múltiplas reviews no mesmo order_id deduplicadas)",
            "SELECT COUNT(*) - COUNT(DISTINCT order_id) FROM staging.stg_order_reviews;"
        ),
        (
            "R10 - Pedidos sem data de entrega ao cliente (mapeados para sk_tempo_entrega = -1)",
            "SELECT COUNT(*) FROM staging.stg_orders WHERE order_delivered_customer_date IS NULL OR TRIM(order_delivered_customer_date) = '';"
        ),
    ]

    with conn.cursor() as cur:
        for descricao, sql in consultas_auditoria:
            cur.execute(sql)
            qtd = cur.fetchone()[0]
            print(f"  * {descricao:<90}: {qtd:>8} linhas")
    print("=" * 110)


def carregar_dimensoes(conn):
    """Carrega e atualiza (idempotente via ON CONFLICT) todas as dimensões do esquema dw."""
    inicio = time.time()
    print("\n[1/2] CARREGANDO DIMENSÕES NO ESQUEMA DW (LOOKUP & UPSERT IDEMPOTENTE)...")

    sql_dimensoes = """
    -- Tabela temporária de geolocalização deduplicada por prefixo de CEP e fallback por UF
    DROP TABLE IF EXISTS pg_temp.tmp_geo_cep;
    CREATE TEMP TABLE tmp_geo_cep AS
    SELECT
        LPAD(TRIM(geolocation_zip_code_prefix), 5, '0') AS cep_prefixo,
        ROUND(AVG(geolocation_lat), 10) AS lat,
        ROUND(AVG(geolocation_lng), 10) AS lng
    FROM staging.stg_geolocation
    WHERE geolocation_zip_code_prefix IS NOT NULL
    GROUP BY LPAD(TRIM(geolocation_zip_code_prefix), 5, '0');

    CREATE INDEX idx_tmp_geo_cep ON pg_temp.tmp_geo_cep(cep_prefixo);

    DROP TABLE IF EXISTS pg_temp.tmp_geo_uf;
    CREATE TEMP TABLE tmp_geo_uf AS
    SELECT
        UPPER(TRIM(geolocation_state)) AS uf,
        ROUND(AVG(geolocation_lat), 10) AS lat,
        ROUND(AVG(geolocation_lng), 10) AS lng
    FROM staging.stg_geolocation
    WHERE geolocation_state IS NOT NULL
    GROUP BY UPPER(TRIM(geolocation_state));

    -- 1. Carga de dw.dim_cliente
    INSERT INTO dw.dim_cliente (
        nk_customer_id, customer_unique_id, cep_prefixo_cliente,
        cidade_cliente, uf_cliente, regiao_cliente, latitude_cliente, longitude_cliente
    )
    SELECT
        TRIM(c.customer_id) AS nk_customer_id,
        TRIM(c.customer_unique_id) AS customer_unique_id,
        LPAD(TRIM(c.customer_zip_code_prefix), 5, '0') AS cep_prefixo_cliente,
        COALESCE(
            NULLIF(INITCAP(REGEXP_REPLACE(TRIM(TRANSLATE(LOWER(c.customer_city),
                'áàâãäéèêëíìîïóòôõöúùûüçñ''/-',
                'aaaaaeeeeiiiiooooouuuucn   ')), '\\s+', ' ', 'g')), ''),
            'Desconhecida'
        ) AS cidade_cliente,
        UPPER(TRIM(c.customer_state)) AS uf_cliente,
        CASE UPPER(TRIM(c.customer_state))
            WHEN 'AC' THEN 'Norte' WHEN 'AP' THEN 'Norte' WHEN 'AM' THEN 'Norte'
            WHEN 'PA' THEN 'Norte' WHEN 'RO' THEN 'Norte' WHEN 'RR' THEN 'Norte' WHEN 'TO' THEN 'Norte'
            WHEN 'AL' THEN 'Nordeste' WHEN 'BA' THEN 'Nordeste' WHEN 'CE' THEN 'Nordeste'
            WHEN 'MA' THEN 'Nordeste' WHEN 'PB' THEN 'Nordeste' WHEN 'PE' THEN 'Nordeste'
            WHEN 'PI' THEN 'Nordeste' WHEN 'RN' THEN 'Nordeste' WHEN 'SE' THEN 'Nordeste'
            WHEN 'DF' THEN 'Centro-Oeste' WHEN 'GO' THEN 'Centro-Oeste'
            WHEN 'MT' THEN 'Centro-Oeste' WHEN 'MS' THEN 'Centro-Oeste'
            WHEN 'ES' THEN 'Sudeste' WHEN 'MG' THEN 'Sudeste'
            WHEN 'RJ' THEN 'Sudeste' WHEN 'SP' THEN 'Sudeste'
            WHEN 'PR' THEN 'Sul' WHEN 'RS' THEN 'Sul' WHEN 'SC' THEN 'Sul'
            ELSE 'Desconhecida'
        END AS regiao_cliente,
        COALESCE(g.lat, guf.lat, 0.0) AS latitude_cliente,
        COALESCE(g.lng, guf.lng, 0.0) AS longitude_cliente
    FROM staging.stg_customers c
    LEFT JOIN pg_temp.tmp_geo_cep g
        ON LPAD(TRIM(c.customer_zip_code_prefix), 5, '0') = g.cep_prefixo
    LEFT JOIN pg_temp.tmp_geo_uf guf
        ON UPPER(TRIM(c.customer_state)) = guf.uf
    ON CONFLICT (nk_customer_id) DO UPDATE SET
        customer_unique_id = EXCLUDED.customer_unique_id,
        cep_prefixo_cliente = EXCLUDED.cep_prefixo_cliente,
        cidade_cliente = EXCLUDED.cidade_cliente,
        uf_cliente = EXCLUDED.uf_cliente,
        regiao_cliente = EXCLUDED.regiao_cliente,
        latitude_cliente = EXCLUDED.latitude_cliente,
        longitude_cliente = EXCLUDED.longitude_cliente;

    -- 2. Carga de dw.dim_vendedor
    INSERT INTO dw.dim_vendedor (
        nk_seller_id, cep_prefixo_vendedor,
        cidade_vendedor, uf_vendedor, regiao_vendedor, latitude_vendedor, longitude_vendedor
    )
    SELECT
        TRIM(s.seller_id) AS nk_seller_id,
        LPAD(TRIM(s.seller_zip_code_prefix), 5, '0') AS cep_prefixo_vendedor,
        COALESCE(
            NULLIF(INITCAP(REGEXP_REPLACE(TRIM(TRANSLATE(LOWER(s.seller_city),
                'áàâãäéèêëíìîïóòôõöúùûüçñ''/-',
                'aaaaaeeeeiiiiooooouuuucn   ')), '\\s+', ' ', 'g')), ''),
            'Desconhecida'
        ) AS cidade_vendedor,
        UPPER(TRIM(s.seller_state)) AS uf_vendedor,
        CASE UPPER(TRIM(s.seller_state))
            WHEN 'AC' THEN 'Norte' WHEN 'AP' THEN 'Norte' WHEN 'AM' THEN 'Norte'
            WHEN 'PA' THEN 'Norte' WHEN 'RO' THEN 'Norte' WHEN 'RR' THEN 'Norte' WHEN 'TO' THEN 'Norte'
            WHEN 'AL' THEN 'Nordeste' WHEN 'BA' THEN 'Nordeste' WHEN 'CE' THEN 'Nordeste'
            WHEN 'MA' THEN 'Nordeste' WHEN 'PB' THEN 'Nordeste' WHEN 'PE' THEN 'Nordeste'
            WHEN 'PI' THEN 'Nordeste' WHEN 'RN' THEN 'Nordeste' WHEN 'SE' THEN 'Nordeste'
            WHEN 'DF' THEN 'Centro-Oeste' WHEN 'GO' THEN 'Centro-Oeste'
            WHEN 'MT' THEN 'Centro-Oeste' WHEN 'MS' THEN 'Centro-Oeste'
            WHEN 'ES' THEN 'Sudeste' WHEN 'MG' THEN 'Sudeste'
            WHEN 'RJ' THEN 'Sudeste' WHEN 'SP' THEN 'Sudeste'
            WHEN 'PR' THEN 'Sul' WHEN 'RS' THEN 'Sul' WHEN 'SC' THEN 'Sul'
            ELSE 'Desconhecida'
        END AS regiao_vendedor,
        COALESCE(g.lat, guf.lat, 0.0) AS latitude_vendedor,
        COALESCE(g.lng, guf.lng, 0.0) AS longitude_vendedor
    FROM staging.stg_sellers s
    LEFT JOIN pg_temp.tmp_geo_cep g
        ON LPAD(TRIM(s.seller_zip_code_prefix), 5, '0') = g.cep_prefixo
    LEFT JOIN pg_temp.tmp_geo_uf guf
        ON UPPER(TRIM(s.seller_state)) = guf.uf
    ON CONFLICT (nk_seller_id) DO UPDATE SET
        cep_prefixo_vendedor = EXCLUDED.cep_prefixo_vendedor,
        cidade_vendedor = EXCLUDED.cidade_vendedor,
        uf_vendedor = EXCLUDED.uf_vendedor,
        regiao_vendedor = EXCLUDED.regiao_vendedor,
        latitude_vendedor = EXCLUDED.latitude_vendedor,
        longitude_vendedor = EXCLUDED.longitude_vendedor;

    -- 3. Carga de dw.dim_produto
    INSERT INTO dw.dim_produto (
        nk_product_id, categoria_pt, categoria_en,
        peso_gramas, comprimento_cm, altura_cm, largura_cm, volume_cm3, qtd_fotos
    )
    SELECT
        TRIM(p.product_id) AS nk_product_id,
        COALESCE(NULLIF(TRIM(p.product_category_name), ''), 'Nao Informada') AS categoria_pt,
        COALESCE(
            NULLIF(TRIM(t.product_category_name_english), ''),
            CASE TRIM(p.product_category_name)
                WHEN 'pc_gamer' THEN 'pc_gamer'
                WHEN 'portateis_cozinha_e_preparadores_de_alimentos' THEN 'kitchen_laptops_and_food_preparers'
                ELSE 'Uninformed'
            END
        ) AS categoria_en,
        COALESCE(p.product_weight_g, 0.0) AS peso_gramas,
        COALESCE(p.product_length_cm, 0.0) AS comprimento_cm,
        COALESCE(p.product_height_cm, 0.0) AS altura_cm,
        COALESCE(p.product_width_cm, 0.0) AS largura_cm,
        ROUND(COALESCE(p.product_length_cm, 0.0) * COALESCE(p.product_height_cm, 0.0) * COALESCE(p.product_width_cm, 0.0), 2) AS volume_cm3,
        COALESCE(p.product_photos_qty::INTEGER, 0) AS qtd_fotos
    FROM staging.stg_products p
    LEFT JOIN staging.stg_category_translation t
        ON TRIM(p.product_category_name) = TRIM(t.product_category_name)
    ON CONFLICT (nk_product_id) DO UPDATE SET
        categoria_pt = EXCLUDED.categoria_pt,
        categoria_en = EXCLUDED.categoria_en,
        peso_gramas = EXCLUDED.peso_gramas,
        comprimento_cm = EXCLUDED.comprimento_cm,
        altura_cm = EXCLUDED.altura_cm,
        largura_cm = EXCLUDED.largura_cm,
        volume_cm3 = EXCLUDED.volume_cm3,
        qtd_fotos = EXCLUDED.qtd_fotos;

    -- 4. Carga de dw.dim_status_pedido
    INSERT INTO dw.dim_status_pedido (
        nk_status_codigo, status_pedido_original, status_pedido_pt, status_pontualidade_entrega
    )
    SELECT DISTINCT
        TRIM(o.order_status) || '|' ||
        CASE
            WHEN o.order_delivered_customer_date IS NULL OR TRIM(o.order_delivered_customer_date) = '' THEN 'Nao Entregue'
            WHEN o.order_delivered_customer_date::TIMESTAMP::DATE > o.order_estimated_delivery_date::TIMESTAMP::DATE THEN 'Atrasado'
            ELSE 'No Prazo'
        END AS nk_status_codigo,
        TRIM(o.order_status) AS status_pedido_original,
        CASE TRIM(o.order_status)
            WHEN 'delivered' THEN 'Entregue'
            WHEN 'shipped' THEN 'Enviado'
            WHEN 'canceled' THEN 'Cancelado'
            WHEN 'unavailable' THEN 'Indisponivel'
            WHEN 'invoiced' THEN 'Faturado'
            WHEN 'processing' THEN 'Em Processamento'
            WHEN 'created' THEN 'Criado'
            WHEN 'approved' THEN 'Aprovado'
            ELSE 'Outros'
        END AS status_pedido_pt,
        CASE
            WHEN o.order_delivered_customer_date IS NULL OR TRIM(o.order_delivered_customer_date) = '' THEN 'Nao Entregue'
            WHEN o.order_delivered_customer_date::TIMESTAMP::DATE > o.order_estimated_delivery_date::TIMESTAMP::DATE THEN 'Atrasado'
            ELSE 'No Prazo'
        END AS status_pontualidade_entrega
    FROM staging.stg_orders o
    ON CONFLICT (nk_status_codigo) DO UPDATE SET
        status_pedido_original = EXCLUDED.status_pedido_original,
        status_pedido_pt = EXCLUDED.status_pedido_pt,
        status_pontualidade_entrega = EXCLUDED.status_pontualidade_entrega;

    -- 5. Carga de dw.dim_tipo_pagamento
    INSERT INTO dw.dim_tipo_pagamento (
        nk_payment_type, tipo_pagamento_original, tipo_pagamento_pt, modalidade_cobranca
    )
    SELECT DISTINCT
        TRIM(p.payment_type) AS nk_payment_type,
        TRIM(p.payment_type) AS tipo_pagamento_original,
        CASE TRIM(p.payment_type)
            WHEN 'credit_card' THEN 'Cartao de Credito'
            WHEN 'boleto' THEN 'Boleto Bancario'
            WHEN 'voucher' THEN 'Voucher / Vale'
            WHEN 'debit_card' THEN 'Cartao de Debito'
            WHEN 'not_defined' THEN 'Nao Definido'
            ELSE 'Outros'
        END AS tipo_pagamento_pt,
        CASE TRIM(p.payment_type)
            WHEN 'credit_card' THEN 'Credito/Parcelavel'
            WHEN 'boleto' THEN 'A Vista'
            WHEN 'debit_card' THEN 'A Vista'
            WHEN 'voucher' THEN 'A Vista'
            ELSE 'Outros'
        END AS modalidade_cobranca
    FROM staging.stg_order_payments p
    WHERE p.payment_type IS NOT NULL
    ON CONFLICT (nk_payment_type) DO UPDATE SET
        tipo_pagamento_original = EXCLUDED.tipo_pagamento_original,
        tipo_pagamento_pt = EXCLUDED.tipo_pagamento_pt,
        modalidade_cobranca = EXCLUDED.modalidade_cobranca;
    """

    with conn.cursor() as cur:
        cur.execute(sql_dimensoes)
    conn.commit()
    print(f"      Dimensões atualizadas com sucesso em {time.time() - inicio:.2f}s.")


def carregar_fatos(conn, modo="inicial"):
    """
    Carrega as tabelas fato resolvendo chaves substitutas por lookup:
    - modo='inicial': pedidos com order_purchase_timestamp <= '2017-12-31 23:59:59'
    - modo='incremental': pedidos com order_purchase_timestamp > '2017-12-31 23:59:59'
    - modo='completo': todos os períodos (inicial + incremental)
    """
    inicio = time.time()
    if modo == "inicial":
        filtro_data = "o.order_purchase_timestamp::TIMESTAMP <= TIMESTAMP '2017-12-31 23:59:59'"
        desc_modo = "CARGA INICIAL (Pedidos até 31/12/2017)"
    elif modo == "incremental":
        filtro_data = "o.order_purchase_timestamp::TIMESTAMP > TIMESTAMP '2017-12-31 23:59:59'"
        desc_modo = "CARGA INCREMENTAL (Pedidos após 31/12/2017)"
    else:
        filtro_data = "TRUE"
        desc_modo = "CARGA COMPLETA (Todos os períodos)"

    print(f"\n[2/2] EXECUTANDO {desc_modo} NAS TABELAS DE FATOS...")

    sql_fatos = f"""
    -- Tabela temporária de avaliações deduplicadas (1 nota consolidada por order_id: a mais recente)
    DROP TABLE IF EXISTS pg_temp.tmp_reviews_dedup;
    CREATE TEMP TABLE tmp_reviews_dedup AS
    SELECT DISTINCT ON (TRIM(order_id))
        TRIM(order_id) AS order_id,
        review_score::INTEGER AS nota_avaliacao
    FROM staging.stg_order_reviews
    WHERE order_id IS NOT NULL
    ORDER BY
        TRIM(order_id),
        NULLIF(TRIM(review_answer_timestamp), '')::TIMESTAMP DESC NULLS LAST,
        NULLIF(TRIM(review_creation_date), '')::TIMESTAMP DESC NULLS LAST;

    CREATE INDEX idx_tmp_reviews_order ON pg_temp.tmp_reviews_dedup(order_id);

    -- 1. Carga da Fato 1: dw.fato_vendas_itens
    INSERT INTO dw.fato_vendas_itens (
        nk_order_id, nk_order_item_id,
        sk_tempo_compra, sk_tempo_entrega, sk_tempo_estimada,
        sk_cliente, sk_vendedor, sk_produto, sk_status_pedido,
        quantidade_item, valor_preco, valor_frete, valor_total_item,
        dias_para_entrega, dias_atraso_entrega, nota_avaliacao
    )
    SELECT
        TRIM(i.order_id) AS nk_order_id,
        i.order_item_id AS nk_order_item_id,
        COALESCE(tc.sk_tempo, -1) AS sk_tempo_compra,
        COALESCE(te.sk_tempo, -1) AS sk_tempo_entrega,
        COALESCE(tes.sk_tempo, -1) AS sk_tempo_estimada,
        COALESCE(dc.sk_cliente, -1) AS sk_cliente,
        COALESCE(dv.sk_vendedor, -1) AS sk_vendedor,
        COALESCE(dp.sk_produto, -1) AS sk_produto,
        COALESCE(ds.sk_status_pedido, -1) AS sk_status_pedido,
        1 AS quantidade_item,
        COALESCE(i.price, 0.0) AS valor_preco,
        COALESCE(i.freight_value, 0.0) AS valor_frete,
        ROUND(COALESCE(i.price, 0.0) + COALESCE(i.freight_value, 0.0), 2) AS valor_total_item,
        CASE
            WHEN o.order_delivered_customer_date IS NOT NULL AND TRIM(o.order_delivered_customer_date) <> ''
            THEN (o.order_delivered_customer_date::TIMESTAMP::DATE - o.order_purchase_timestamp::TIMESTAMP::DATE)
            ELSE NULL
        END AS dias_para_entrega,
        CASE
            WHEN o.order_delivered_customer_date IS NOT NULL AND TRIM(o.order_delivered_customer_date) <> ''
                 AND o.order_estimated_delivery_date IS NOT NULL AND TRIM(o.order_estimated_delivery_date) <> ''
            THEN (o.order_delivered_customer_date::TIMESTAMP::DATE - o.order_estimated_delivery_date::TIMESTAMP::DATE)
            ELSE NULL
        END AS dias_atraso_entrega,
        rv.nota_avaliacao
    FROM staging.stg_order_items i
    INNER JOIN staging.stg_orders o
        ON TRIM(i.order_id) = TRIM(o.order_id)
    LEFT JOIN dw.dim_tempo tc
        ON tc.data_completa = o.order_purchase_timestamp::TIMESTAMP::DATE
    LEFT JOIN dw.dim_tempo te
        ON te.data_completa = NULLIF(TRIM(o.order_delivered_customer_date), '')::TIMESTAMP::DATE
    LEFT JOIN dw.dim_tempo tes
        ON tes.data_completa = NULLIF(TRIM(o.order_estimated_delivery_date), '')::TIMESTAMP::DATE
    LEFT JOIN dw.dim_cliente dc
        ON dc.nk_customer_id = TRIM(o.customer_id)
    LEFT JOIN dw.dim_vendedor dv
        ON dv.nk_seller_id = TRIM(i.seller_id)
    LEFT JOIN dw.dim_produto dp
        ON dp.nk_product_id = TRIM(i.product_id)
    LEFT JOIN dw.dim_status_pedido ds
        ON ds.nk_status_codigo = (
            TRIM(o.order_status) || '|' ||
            CASE
                WHEN o.order_delivered_customer_date IS NULL OR TRIM(o.order_delivered_customer_date) = '' THEN 'Nao Entregue'
                WHEN o.order_delivered_customer_date::TIMESTAMP::DATE > o.order_estimated_delivery_date::TIMESTAMP::DATE THEN 'Atrasado'
                ELSE 'No Prazo'
            END
        )
    LEFT JOIN pg_temp.tmp_reviews_dedup rv
        ON rv.order_id = TRIM(i.order_id)
    WHERE {filtro_data}
    ON CONFLICT (nk_order_id, nk_order_item_id) DO UPDATE SET
        sk_tempo_compra = EXCLUDED.sk_tempo_compra,
        sk_tempo_entrega = EXCLUDED.sk_tempo_entrega,
        sk_tempo_estimada = EXCLUDED.sk_tempo_estimada,
        sk_cliente = EXCLUDED.sk_cliente,
        sk_vendedor = EXCLUDED.sk_vendedor,
        sk_produto = EXCLUDED.sk_produto,
        sk_status_pedido = EXCLUDED.sk_status_pedido,
        valor_preco = EXCLUDED.valor_preco,
        valor_frete = EXCLUDED.valor_frete,
        valor_total_item = EXCLUDED.valor_total_item,
        dias_para_entrega = EXCLUDED.dias_para_entrega,
        dias_atraso_entrega = EXCLUDED.dias_atraso_entrega,
        nota_avaliacao = EXCLUDED.nota_avaliacao;

    -- 2. Carga da Fato 2: dw.fato_pagamentos_pedido
    INSERT INTO dw.fato_pagamentos_pedido (
        nk_order_id, nk_payment_sequential,
        sk_tempo_compra, sk_cliente, sk_status_pedido, sk_tipo_pagamento,
        valor_pagamento, quantidade_parcelas
    )
    SELECT
        TRIM(p.order_id) AS nk_order_id,
        p.payment_sequential AS nk_payment_sequential,
        COALESCE(tc.sk_tempo, -1) AS sk_tempo_compra,
        COALESCE(dc.sk_cliente, -1) AS sk_cliente,
        COALESCE(ds.sk_status_pedido, -1) AS sk_status_pedido,
        COALESCE(dtp.sk_tipo_pagamento, -1) AS sk_tipo_pagamento,
        COALESCE(p.payment_value, 0.0) AS valor_pagamento,
        COALESCE(p.payment_installments, 1) AS quantidade_parcelas
    FROM staging.stg_order_payments p
    INNER JOIN staging.stg_orders o
        ON TRIM(p.order_id) = TRIM(o.order_id)
    LEFT JOIN dw.dim_tempo tc
        ON tc.data_completa = o.order_purchase_timestamp::TIMESTAMP::DATE
    LEFT JOIN dw.dim_cliente dc
        ON dc.nk_customer_id = TRIM(o.customer_id)
    LEFT JOIN dw.dim_status_pedido ds
        ON ds.nk_status_codigo = (
            TRIM(o.order_status) || '|' ||
            CASE
                WHEN o.order_delivered_customer_date IS NULL OR TRIM(o.order_delivered_customer_date) = '' THEN 'Nao Entregue'
                WHEN o.order_delivered_customer_date::TIMESTAMP::DATE > o.order_estimated_delivery_date::TIMESTAMP::DATE THEN 'Atrasado'
                ELSE 'No Prazo'
            END
        )
    LEFT JOIN dw.dim_tipo_pagamento dtp
        ON dtp.nk_payment_type = TRIM(p.payment_type)
    WHERE {filtro_data}
    ON CONFLICT (nk_order_id, nk_payment_sequential) DO UPDATE SET
        sk_tempo_compra = EXCLUDED.sk_tempo_compra,
        sk_cliente = EXCLUDED.sk_cliente,
        sk_status_pedido = EXCLUDED.sk_status_pedido,
        sk_tipo_pagamento = EXCLUDED.sk_tipo_pagamento,
        valor_pagamento = EXCLUDED.valor_pagamento,
        quantidade_parcelas = EXCLUDED.quantidade_parcelas;
    """

    with conn.cursor() as cur:
        cur.execute(sql_fatos)
    conn.commit()
    print(f"      {desc_modo} concluída em {time.time() - inicio:.2f}s.")


def exibir_resumo_dw(conn, titulo="RESUMO DE CONTAGEM DAS TABELAS DO ESQUEMA DW"):
    print("\n" + "=" * 110)
    print(titulo)
    print("=" * 110)
    tabelas = [
        "dw.dim_tempo",
        "dw.dim_cliente",
        "dw.dim_vendedor",
        "dw.dim_produto",
        "dw.dim_status_pedido",
        "dw.dim_tipo_pagamento",
        "dw.fato_vendas_itens",
        "dw.fato_pagamentos_pedido",
    ]
    with conn.cursor() as cur:
        for t in tabelas:
            cur.execute(f"SELECT COUNT(*) FROM {t};")
            qtd = cur.fetchone()[0]
            print(f"  * {t:<35}: {qtd:>10} registros")
    print("=" * 110)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transformação e Carga do DW Olist")
    parser.add_argument(
        "--modo",
        choices=["inicial", "incremental", "completo"],
        default="inicial",
        help="Modo de carga dos fatos: 'inicial' (até 31/12/2017), 'incremental' (pós-2017) ou 'completo'"
    )
    args = parser.parse_args()

    conn = obter_conexao()
    try:
        auditar_regras_limpeza(conn)
        carregar_dimensoes(conn)
        carregar_fatos(conn, modo=args.modo)
        exibir_resumo_dw(conn, titulo=f"RESUMO DO DW APÓS CARGA ({args.modo.upper()})")
    finally:
        conn.close()