# PARTE 2 — PROJETO LÓGICO, FÍSICO E DICIONÁRIO DE DADOS DO ESQUEMA `dw`

## 1. SGBD Escolhido e Arquitetura de Esquemas
O projeto físico foi implementado no **PostgreSQL 17**. Foram criados dois esquemas distintos no banco `dw_olist`:
- **`staging`** (`ddl/01_create_staging.sql`): 9 tabelas espelhando a estrutura original dos 9 arquivos CSV da Olist, destinadas à carga bruta sem transformações.
- **`dw`** (`ddl/02_create_dw.sql`): 6 tabelas de dimensão (`dim_tempo`, `dim_cliente`, `dim_vendedor`, `dim_produto`, `dim_status_pedido`, `dim_tipo_pagamento`) e 2 tabelas de fatos (`fato_vendas_itens`, `fato_pagamentos_pedido`).

Todas as dimensões possuem chave substituta (`sk_*`), chave natural preservada com restrição `UNIQUE` (`nk_*`), restrições `NOT NULL` e registro de membro desconhecido (`sk = -1`) para impedir chaves estrangeiras nulas nas tabelas de fatos.

---

## 2. Dicionário de Dados do Esquema `dw`

### 2.1. Tabela `dw.dim_tempo`
| Tabela | Coluna | Tipo | Descrição | Origem |
| :--- | :--- | :--- | :--- | :--- |
| `dim_tempo` | `sk_tempo` | `INTEGER` (PK) | Chave substituta no formato `YYYYMMDD` (`-1` para desconhecido) | Gerada por script SQL |
| `dim_tempo` | `data_completa` | `DATE` (UNIQUE) | Data do calendário (`2016-01-01` a `2018-12-31`; `1900-01-01` p/ `-1`) | Gerada via `generate_series` |
| `dim_tempo` | `dia` | `INTEGER` | Dia do mês (1 a 31) | Derivado de `data_completa` |
| `dim_tempo` | `dia_semana_num` | `INTEGER` | Número ISO do dia da semana (1=Segunda a 7=Domingo) | Derivado de `data_completa` |
| `dim_tempo` | `dia_semana_nome` | `VARCHAR(25)` | Nome do dia da semana em português | Derivado de `data_completa` |
| `dim_tempo` | `eh_fim_de_semana` | `VARCHAR(3)` | Indicador de sábado ou domingo (`Sim` / `Nao`) | Derivado de `data_completa` |
| `dim_tempo` | `mes` | `INTEGER` | Número do mês (1 a 12) | Derivado de `data_completa` |
| `dim_tempo` | `nome_mes` | `VARCHAR(20)` | Nome do mês em português | Derivado de `data_completa` |
| `dim_tempo` | `ano_mes` | `VARCHAR(7)` | Ano e mês no formato `YYYY-MM` | Derivado de `data_completa` |
| `dim_tempo` | `trimestre` | `INTEGER` | Número do trimestre (1 a 4) | Derivado de `data_completa` |
| `dim_tempo` | `nome_trimestre` | `VARCHAR(20)` | Descrição do trimestre (`1o Trimestre` a `4o Trimestre`) | Derivado de `data_completa` |
| `dim_tempo` | `ano` | `INTEGER` | Ano civil (`2016`, `2017`, `2018`) | Derivado de `data_completa` |
| `dim_tempo` | `eh_feriado_nacional`| `VARCHAR(3)` | Indicador de feriado nacional brasileiro (`Sim` / `Nao`) | Calendário oficial de feriados |
| `dim_tempo` | `nome_feriado` | `VARCHAR(60)` | Nome do feriado nacional ou `Dia Comum` | Calendário oficial de feriados |

### 2.2. Tabela `dw.dim_cliente`
| Tabela | Coluna | Tipo | Descrição | Origem |
| :--- | :--- | :--- | :--- | :--- |
| `dim_cliente` | `sk_cliente` | `SERIAL` (PK) | Chave substituta da dimensão cliente (`-1` p/ desconhecido) | Gerada no DW |
| `dim_cliente` | `nk_customer_id` | `VARCHAR(50)` | Chave natural do cliente por pedido (`UNIQUE`) | `stg_customers.customer_id` |
| `dim_cliente` | `customer_unique_id` | `VARCHAR(50)` | Identificador único do cliente real na plataforma | `stg_customers.customer_unique_id` |
| `dim_cliente` | `cep_prefixo_cliente`| `VARCHAR(10)` | Prefixo de 5 dígitos do CEP do cliente | `stg_customers.customer_zip_code_prefix` |
| `dim_cliente` | `cidade_cliente` | `VARCHAR(100)`| Nome da cidade do cliente (limpo e padronizado) | `stg_customers.customer_city` |
| `dim_cliente` | `uf_cliente` | `VARCHAR(5)` | Sigla da UF do cliente | `stg_customers.customer_state` |
| `dim_cliente` | `regiao_cliente` | `VARCHAR(20)` | Macro-região brasileira (`Norte`, `Nordeste`, `Sudeste`, `Sul`, `Centro-Oeste`) | Derivado de `customer_state` |
| `dim_cliente` | `latitude_cliente` | `NUMERIC(15,10)`| Latitude consolidada do prefixo de CEP | `stg_geolocation.geolocation_lat` |
| `dim_cliente` | `longitude_cliente` | `NUMERIC(15,10)`| Longitude consolidada do prefixo de CEP | `stg_geolocation.geolocation_lng` |

### 2.3. Tabela `dw.dim_vendedor`
| Tabela | Coluna | Tipo | Descrição | Origem |
| :--- | :--- | :--- | :--- | :--- |
| `dim_vendedor` | `sk_vendedor` | `SERIAL` (PK) | Chave substituta do vendedor (`-1` p/ desconhecido) | Gerada no DW |
| `dim_vendedor` | `nk_seller_id` | `VARCHAR(50)` | Chave natural do vendedor (`UNIQUE`) | `stg_sellers.seller_id` |
| `dim_vendedor` | `cep_prefixo_vendedor`| `VARCHAR(10)` | Prefixo de 5 dígitos do CEP do vendedor | `stg_sellers.seller_zip_code_prefix` |
| `dim_vendedor` | `cidade_vendedor` | `VARCHAR(100)`| Nome da cidade do vendedor (limpo e padronizado) | `stg_sellers.seller_city` |
| `dim_vendedor` | `uf_vendedor` | `VARCHAR(5)` | Sigla da UF do vendedor | `stg_sellers.seller_state` |
| `dim_vendedor` | `regiao_vendedor` | `VARCHAR(20)` | Macro-região brasileira do vendedor | Derivado de `seller_state` |
| `dim_vendedor` | `latitude_vendedor` | `NUMERIC(15,10)`| Latitude consolidada do prefixo de CEP | `stg_geolocation.geolocation_lat` |
| `dim_vendedor` | `longitude_vendedor` | `NUMERIC(15,10)`| Longitude consolidada do prefixo de CEP | `stg_geolocation.geolocation_lng` |

### 2.4. Tabela `dw.dim_produto`
| Tabela | Coluna | Tipo | Descrição | Origem |
| :--- | :--- | :--- | :--- | :--- |
| `dim_produto` | `sk_produto` | `SERIAL` (PK) | Chave substituta do produto (`-1` p/ desconhecido) | Gerada no DW |
| `dim_produto` | `nk_product_id` | `VARCHAR(50)` | Chave natural do produto (`UNIQUE`) | `stg_products.product_id` |
| `dim_produto` | `categoria_pt` | `VARCHAR(100)`| Categoria em português (`Nao Informada` quando ausente) | `stg_products.product_category_name` |
| `dim_produto` | `categoria_en` | `VARCHAR(100)`| Categoria traduzida para inglês (`Uninformed` quando ausente) | `stg_category_translation.product_category_name_english` |
| `dim_produto` | `peso_gramas` | `NUMERIC(12,2)`| Peso do produto em gramas | `stg_products.product_weight_g` |
| `dim_produto` | `comprimento_cm` | `NUMERIC(10,2)`| Comprimento da embalagem em centímetros | `stg_products.product_length_cm` |
| `dim_produto` | `altura_cm` | `NUMERIC(10,2)`| Altura da embalagem em centímetros | `stg_products.product_height_cm` |
| `dim_produto` | `largura_cm` | `NUMERIC(10,2)`| Largura da embalagem em centímetros | `stg_products.product_width_cm` |
| `dim_produto` | `volume_cm3` | `NUMERIC(14,2)`| Volume cúbico calculado (`comprimento * altura * largura`) | Derivado no ETL |
| `dim_produto` | `qtd_fotos` | `INTEGER` | Quantidade de fotos do anúncio do produto | `stg_products.product_photos_qty` |

### 2.5. Tabela `dw.dim_status_pedido`
| Tabela | Coluna | Tipo | Descrição | Origem |
| :--- | :--- | :--- | :--- | :--- |
| `dim_status_pedido`| `sk_status_pedido` | `SERIAL` (PK) | Chave substituta do status (`-1` p/ desconhecido) | Gerada no DW |
| `dim_status_pedido`| `nk_status_codigo` | `VARCHAR(60)` | Chave natural composta (`status_original|pontualidade`) | Derivado de `stg_orders` |
| `dim_status_pedido`| `status_pedido_original`| `VARCHAR(30)`| Código original do status do pedido em inglês | `stg_orders.order_status` |
| `dim_status_pedido`| `status_pedido_pt` | `VARCHAR(40)` | Tradução do status do pedido para português | Decodificado no ETL |
| `dim_status_pedido`| `status_pontualidade_entrega`| `VARCHAR(30)`| Situação do prazo (`No Prazo`, `Atrasado`, `Nao Entregue`) | Derivado das datas de entrega de `stg_orders` |

### 2.6. Tabela `dw.dim_tipo_pagamento`
| Tabela | Coluna | Tipo | Descrição | Origem |
| :--- | :--- | :--- | :--- | :--- |
| `dim_tipo_pagamento`| `sk_tipo_pagamento` | `SERIAL` (PK) | Chave substituta do tipo de pagamento (`-1` p/ desconhecido) | Gerada no DW |
| `dim_tipo_pagamento`| `nk_payment_type` | `VARCHAR(30)` | Chave natural do meio de pagamento (`UNIQUE`) | `stg_order_payments.payment_type` |
| `dim_tipo_pagamento`| `tipo_pagamento_original`| `VARCHAR(30)`| Nome original do meio de pagamento | `stg_order_payments.payment_type` |
| `dim_tipo_pagamento`| `tipo_pagamento_pt` | `VARCHAR(40)` | Descrição padronizada em português | Decodificado no ETL |
| `dim_tipo_pagamento`| `modalidade_cobranca`| `VARCHAR(30)` | Classificação (`Credito/Parcelavel`, `A Vista`, `Outros`) | Derivado de `payment_type` |

### 2.7. Tabela Fato `dw.fato_vendas_itens`
| Tabela | Coluna | Tipo | Descrição | Origem |
| :--- | :--- | :--- | :--- | :--- |
| `fato_vendas_itens` | `sk_fato_item` | `SERIAL` (PK) | Chave substituta da linha da tabela fato | Gerada no DW |
| `fato_vendas_itens` | `nk_order_id` | `VARCHAR(50)` | Identificador do pedido (dimensão degenerada, compõe UNIQUE do grão) | `stg_order_items.order_id` |
| `fato_vendas_itens` | `nk_order_item_id` | `INTEGER` | Sequencial do item no pedido (compõe UNIQUE do grão) | `stg_order_items.order_item_id` |
| `fato_vendas_itens` | `sk_tempo_compra` | `INTEGER` (FK) | FK para `dim_tempo` referente à data da compra | Lookup `stg_orders.order_purchase_timestamp` |
| `fato_vendas_itens` | `sk_tempo_entrega` | `INTEGER` (FK) | FK para `dim_tempo` referente à data de entrega (`-1` se ausente) | Lookup `stg_orders.order_delivered_customer_date` |
| `fato_vendas_itens` | `sk_tempo_estimada` | `INTEGER` (FK) | FK para `dim_tempo` referente à data estimada de entrega | Lookup `stg_orders.order_estimated_delivery_date` |
| `fato_vendas_itens` | `sk_cliente` | `INTEGER` (FK) | FK para `dim_cliente` | Lookup `stg_orders.customer_id` |
| `fato_vendas_itens` | `sk_vendedor` | `INTEGER` (FK) | FK para `dim_vendedor` | Lookup `stg_order_items.seller_id` |
| `fato_vendas_itens` | `sk_produto` | `INTEGER` (FK) | FK para `dim_produto` | Lookup `stg_order_items.product_id` |
| `fato_vendas_itens` | `sk_status_pedido` | `INTEGER` (FK) | FK para `dim_status_pedido` | Lookup `stg_orders` |
| `fato_vendas_itens` | `quantidade_item` | `INTEGER` | Medida aditiva: quantidade de itens (1 por linha) | Constante `1` no grão do item |
| `fato_vendas_itens` | `valor_preco` | `NUMERIC(12,2)`| Medida aditiva: preço unitário do item vendido | `stg_order_items.price` |
| `fato_vendas_itens` | `valor_frete` | `NUMERIC(12,2)`| Medida aditiva: valor de frete do item | `stg_order_items.freight_value` |
| `fato_vendas_itens` | `valor_total_item` | `NUMERIC(12,2)`| Medida aditiva: soma `valor_preco + valor_frete` | Derivado no ETL |
| `fato_vendas_itens` | `dias_para_entrega` | `INTEGER` | Medida não aditiva: dias corridos entre compra e entrega real | Derivado de `stg_orders` |
| `fato_vendas_itens` | `dias_atraso_entrega`| `INTEGER` | Medida não aditiva: dias corridos entre entrega real e estimada | Derivado de `stg_orders` |
| `fato_vendas_itens` | `nota_avaliacao` | `INTEGER` | Medida não aditiva: nota de satisfação consolidada do pedido (1 a 5) | `stg_order_reviews.review_score` (deduplicada) |

### 2.8. Tabela Fato `dw.fato_pagamentos_pedido`
| Tabela | Coluna | Tipo | Descrição | Origem |
| :--- | :--- | :--- | :--- | :--- |
| `fato_pagamentos_pedido`| `sk_fato_pagamento` | `SERIAL` (PK) | Chave substituta da linha de pagamento | Gerada no DW |
| `fato_pagamentos_pedido`| `nk_order_id` | `VARCHAR(50)` | Identificador do pedido (dimensão degenerada, compõe UNIQUE) | `stg_order_payments.order_id` |
| `fato_pagamentos_pedido`| `nk_payment_sequential`| `INTEGER` | Sequencial da transação de pagamento no pedido (compõe UNIQUE) | `stg_order_payments.payment_sequential` |
| `fato_pagamentos_pedido`| `sk_tempo_compra` | `INTEGER` (FK) | FK para `dim_tempo` referente à data da compra do pedido | Lookup `stg_orders.order_purchase_timestamp` |
| `fato_pagamentos_pedido`| `sk_cliente` | `INTEGER` (FK) | FK para `dim_cliente` | Lookup `stg_orders.customer_id` |
| `fato_pagamentos_pedido`| `sk_status_pedido` | `INTEGER` (FK) | FK para `dim_status_pedido` | Lookup `stg_orders` |
| `fato_pagamentos_pedido`| `sk_tipo_pagamento` | `INTEGER` (FK) | FK para `dim_tipo_pagamento` | Lookup `stg_order_payments.payment_type` |
| `fato_pagamentos_pedido`| `valor_pagamento` | `NUMERIC(12,2)`| Medida aditiva: valor pago na transação/sequencial | `stg_order_payments.payment_value` |
| `fato_pagamentos_pedido`| `quantidade_parcelas`| `INTEGER` | Medida não aditiva: número de parcelas da transação | `stg_order_payments.payment_installments` |