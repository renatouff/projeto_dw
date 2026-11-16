# PARTE 1 — REQUISITOS ANALÍTICOS E MODELAGEM DIMENSIONAL (DW OLIST)

## 1. Contexto e Análise da Base Operacional
O Data Warehouse (DW) foi projetado a partir do conjunto de dados *Brazilian E-Commerce Public Dataset by Olist* (licença CC BY-NC-SA 4.0), composto por 9 arquivos CSV operacionais que registram 99.441 pedidos realizados entre setembro de 2016 e outubro de 2018.

A inspeção técnica dos arquivos de origem evidenciou diferentes granularidades operacionais que impedem a unificação em uma única tabela fato sem gerar multiplicação indevida de registros (*fan trap*):
- Existem **9.803 pedidos com mais de 1 item** (`112.650` linhas em `olist_order_items_dataset.csv` para `98.666` pedidos distintos com itens) e **1.278 pedidos com múltiplos vendedores**.
- Existem **2.961 pedidos com mais de 1 registro de pagamento** (`103.886` linhas em `olist_order_payments_dataset.csv`).
- O identificador `customer_id` muda a cada pedido (`99.441` valores), enquanto o cliente real é identificado por `customer_unique_id` (`96.096` clientes únicos).

Para atender às necessidades analíticas da diretoria (vendas, logística de entrega, meios de pagamento e satisfação dos clientes) sem distorcer somas financeiras, foram modeladas **duas tabelas de fatos** que compartilham **dimensões conformadas**, sem ligação direta entre fatos.

---

## 2. Dez Perguntas Analíticas de Negócio

1. **[Vendas — Evolução Temporal e Subtotais]** Qual é a evolução mensal, trimestral e anual da receita de produtos, do valor total de frete e do faturamento total dos itens vendidos, incluindo subtotais hierárquicos (`ROLLUP`)?
   - **Métricas:** `SUM(valor_preco)`, `SUM(valor_frete)`, `SUM(valor_total_item)` (aditivas).
   - **Recortes:** `dim_tempo` (`ano`, `trimestre`, `mes`).
2. **[Vendas — Desempenho por Categoria]** Quais são as 10 categorias de produtos (em português e inglês) com maior receita acumulada de vendas, qual o volume de itens vendidos e o ticket médio por item em cada categoria?
   - **Métricas:** `SUM(valor_preco)`, `SUM(quantidade_item)` (aditivas); `AVG(valor_preco)` (não aditiva).
   - **Recortes:** `dim_produto` (`categoria_pt`, `categoria_en`).
3. **[Vendas — Distribuição Geográfica]** Como se distribuem a receita de produtos e o valor de frete por Região e UF de destino do cliente, considerando subtotais regionais e total geral (`GROUPING SETS` / `ROLLUP`)?
   - **Métricas:** `SUM(valor_preco)`, `SUM(valor_frete)` (aditivas).
   - **Recortes:** `dim_cliente` (`regiao_cliente`, `uf_cliente`).
4. **[Vendas — Ranking de Vendedores]** Quais são os 10 vendedores com maior receita de vendas, quantos itens cada um comercializou e qual sua localização (cidade, UF e região)?
   - **Métricas:** `SUM(valor_preco)`, `SUM(quantidade_item)` (aditivas).
   - **Recortes:** `dim_vendedor` (`nk_seller_id`, `cidade_vendedor`, `uf_vendedor`, `regiao_vendedor`).
5. **[Vendas — Calendário e Feriados Nacionais]** Qual é o faturamento total, o volume de itens vendidos e a média de faturamento por dia de calendário em dias úteis, finais de semana e feriados nacionais?
   - **Métricas:** `SUM(valor_total_item)`, `SUM(quantidade_item)` (aditivas); `SUM(valor_total_item) / COUNT(DISTINCT sk_tempo_compra)` (semiaditiva/derivada).
   - **Recortes:** `dim_tempo` (`eh_feriado_nacional`, `eh_fim_de_semana`, `dia_semana_nome`).
6. **[Vendas — Recorrência e Fidelidade de Clientes]** Quantos clientes reais (`customer_unique_id`) realizaram mais de um pedido na plataforma e qual é o ticket médio gasto por cliente recorrente em comparação aos clientes de compra única por região?
   - **Métricas:** `COUNT(DISTINCT nk_order_id)`, `COUNT(DISTINCT customer_unique_id)`, `SUM(valor_total_item)`.
   - **Recortes:** `dim_cliente` (`customer_unique_id`, `regiao_cliente`).
7. **[Logística — Prazos de Entrega por Região e UF]** Qual é o tempo médio real de entrega (em dias) e a diferença média em dias em relação à data estimada de entrega por Região e UF do cliente nos pedidos entregues?
   - **Métricas:** `AVG(dias_para_entrega)`, `AVG(dias_atraso_entrega)` (não aditivas).
   - **Recortes:** `dim_cliente` (`regiao_cliente`, `uf_cliente`), `dim_status_pedido` (`status_pedido_original`).
8. **[Logística — Evolução da Taxa de Atraso e Frete]** Qual é o percentual mensal de itens entregues com atraso (data de entrega posterior à data estimada) e como se comporta o valor médio de frete nesses meses?
   - **Métricas:** Taxa percentual de atraso (não aditiva), `AVG(valor_frete)` (não aditiva).
   - **Recortes:** `dim_tempo` (`ano`, `mes`), `dim_status_pedido` (`status_pontualidade_entrega`).
9. **[Meios de Pagamento — Modalidades e Parcelamento]** Qual é o valor total transacionado, a participação percentual na receita de pagamentos e a média de parcelas contratadas por tipo de pagamento e trimestre (`CUBE` / agrupamento multidimensional)?
   - **Métricas:** `SUM(valor_pagamento)` (aditiva), `AVG(quantidade_parcelas)` (não aditiva).
   - **Recortes:** `dim_tipo_pagamento` (`tipo_pagamento_pt`, `modalidade_cobranca`), `dim_tempo` (`ano`, `trimestre`).
10. **[Satisfação dos Clientes — Impacto Logístico nas Avaliações]** Qual é a nota média de avaliação (`nota_avaliacao`) dos pedidos segundo a pontualidade da entrega (No Prazo vs. Atrasado) e as principais categorias de produto?
    - **Métricas:** `AVG(nota_avaliacao)`, `AVG(dias_para_entrega)` (não aditivas).
    - **Recortes:** `dim_status_pedido` (`status_pontualidade_entrega`), `dim_produto` (`categoria_pt`).

---

## 3. Especificação das Tabelas de Fatos

### 3.1. `fato_vendas_itens`
- **Grão:** Uma linha por item de pedido comercializado (`order_id` + `order_item_id`), registrando os valores financeiros do item, os prazos logísticos e a avaliação associada ao pedido.
- **Chaves Estrangeiras (Dimensões):** `sk_tempo_compra`, `sk_tempo_entrega`, `sk_tempo_estimada` (referenciando `dim_tempo`), `sk_cliente`, `sk_vendedor`, `sk_produto`, `sk_status_pedido`.
- **Dimensões Degeneradas:** `nk_order_id`, `nk_order_item_id`.
- **Medidas e Classificação:**
  - `quantidade_item` (INTEGER, valor `1` por item): **Aditiva** — pode ser somada em todas as dimensões.
  - `valor_preco` (NUMERIC): **Aditiva** — receita bruta do item, somável em todas as dimensões.
  - `valor_frete` (NUMERIC): **Aditiva** — frete do item, somável em todas as dimensões.
  - `valor_total_item` (NUMERIC, `valor_preco + valor_frete`): **Aditiva** — faturamento total do item.
  - `dias_para_entrega` (INTEGER): **Não aditiva** — diferença em dias entre entrega e compra; agregada por `AVG`, `MIN` ou `MAX`.
  - `dias_atraso_entrega` (INTEGER): **Não aditiva** — diferença em dias entre entrega real e estimada; agregada por `AVG`.
  - `nota_avaliacao` (INTEGER, 1 a 5): **Não aditiva** — nota da avaliação consolidada do pedido; agregada por `AVG`.

### 3.2. `fato_pagamentos_pedido`
- **Grão:** Uma linha por sequencial de pagamento de um pedido (`order_id` + `payment_sequential`).
- **Chaves Estrangeiras (Dimensões):** `sk_tempo_compra` (`dim_tempo`), `sk_cliente`, `sk_status_pedido`, `sk_tipo_pagamento`.
- **Dimensões Degeneradas:** `nk_order_id`, `nk_payment_sequential`.
- **Medidas e Classificação:**
  - `valor_pagamento` (NUMERIC): **Aditiva** — valor monetário da transação de pagamento, somável em todas as dimensões.
  - `quantidade_parcelas` (INTEGER): **Não aditiva** — número de parcelas escolhidas na transação; analisada via `AVG` ou `MAX`.

---

## 4. Especificação das Dimensões e Hierarquias

Todas as dimensões possuem chave substituta inteira (`sk_*`), preservam a chave natural (`nk_*`) e contêm o registro de membro desconhecido (`sk = -1`) para evitar chaves estrangeiras nulas nos fatos:

1. **`dim_tempo` (Conformada):**
   - **PK:** `sk_tempo` | **NK:** `data_completa` (`DATE`, 2016-01-01 a 2018-12-31).
   - **Atributos:** `dia`, `dia_semana_num`, `dia_semana_nome`, `eh_fim_de_semana`, `mes`, `nome_mes`, `ano_mes`, `trimestre`, `nome_trimestre`, `ano`, `eh_feriado_nacional`, `nome_feriado`.
   - **Hierarquia:** `data_completa (dia) > mes > trimestre > ano`.
2. **`dim_cliente` (Conformada):**
   - **PK:** `sk_cliente` | **NK:** `nk_customer_id` (com atributo `customer_unique_id` identificando o cliente real).
   - **Atributos:** `customer_unique_id`, `cep_prefixo_cliente`, `cidade_cliente`, `uf_cliente`, `regiao_cliente`, `latitude_cliente`, `longitude_cliente`.
   - **Hierarquia:** `cep_prefixo_cliente > cidade_cliente > uf_cliente > regiao_cliente`.
3. **`dim_vendedor`:**
   - **PK:** `sk_vendedor` | **NK:** `nk_seller_id`.
   - **Atributos:** `cep_prefixo_vendedor`, `cidade_vendedor`, `uf_vendedor`, `regiao_vendedor`, `latitude_vendedor`, `longitude_vendedor`.
   - **Hierarquia:** `cep_prefixo_vendedor > cidade_vendedor > uf_vendedor > regiao_vendedor`.
4. **`dim_produto`:**
   - **PK:** `sk_produto` | **NK:** `nk_product_id`.
   - **Atributos:** `categoria_pt`, `categoria_en`, `peso_gramas`, `comprimento_cm`, `altura_cm`, `largura_cm`, `volume_cm3`, `qtd_fotos`.
   - **Hierarquia:** `nk_product_id (produto) > categoria_pt / categoria_en`.
5. **`dim_status_pedido` (Conformada):**
   - **PK:** `sk_status_pedido` | **NK:** `nk_status_codigo`.
   - **Atributos:** `status_pedido_original`, `status_pedido_pt`, `status_pontualidade_entrega`.
   - **Hierarquia:** `status_pedido_pt > status_pontualidade_entrega`.
6. **`dim_tipo_pagamento`:**
   - **PK:** `sk_tipo_pagamento` | **NK:** `nk_payment_type`.
   - **Atributos:** `tipo_pagamento_original`, `tipo_pagamento_pt`, `modalidade_cobranca`.
   - **Hierarquia:** `tipo_pagamento_pt > modalidade_cobranca`.

---

## 5. Justificativa: Esquema Estrela (*Star Schema*) vs. Floco de Neve (*Snowflake*)

Adotou-se o **Esquema Estrela (*Star Schema*)** com hierarquias consolidadas (dimensões desnormalizadas) em vez do modelo Floco de Neve (*Snowflake*) pelos seguintes critérios fundamentados em aula:
1. **Desempenho e simplicidade de consultas:** A consolidação das hierarquias geográficas (`cidade > UF > região` e coordenadas) e de categoria (`categoria_pt` e `categoria_en`) diretamente nas dimensões elimina `JOINs` adicionais durante o processamento analítico (OLAP).
2. **Clareza do modelo:** Estruturas em estrela são mais intuitivas para navegação e construção de consultas SQL com operadores `ROLLUP`, `CUBE` e `GROUPING SETS`.
3. **Baixo custo de armazenamento:** Como a cardinalidade das dimensões é reduzida frente às tabelas de fatos, a desnormalização das hierarquias tem impacto desprezível em espaço de disco.
4. **Dimensões conformadas:** As tabelas `fato_vendas_itens` e `fato_pagamentos_pedido` compartilham `dim_tempo`, `dim_cliente` e `dim_status_pedido`, sem relacionamento direto entre tabelas de fatos.

---

## 6. Matriz de Rastreabilidade

| Pergunta | Tabela Fato | Medidas Utilizadas | Dimensões Utilizadas |
| :--- | :--- | :--- | :--- |
| **P01** | `fato_vendas_itens` | `valor_preco`, `valor_frete`, `valor_total_item` | `dim_tempo` |
| **P02** | `fato_vendas_itens` | `valor_preco`, `quantidade_item` | `dim_produto` |
| **P03** | `fato_vendas_itens` | `valor_preco`, `valor_frete` | `dim_cliente` |
| **P04** | `fato_vendas_itens` | `valor_preco`, `quantidade_item` | `dim_vendedor` |
| **P05** | `fato_vendas_itens` | `valor_total_item`, `quantidade_item` | `dim_tempo` |
| **P06** | `fato_vendas_itens` | `valor_total_item`, `nk_order_id` | `dim_cliente` |
| **P07** | `fato_vendas_itens` | `dias_para_entrega`, `dias_atraso_entrega` | `dim_cliente`, `dim_status_pedido` |
| **P08** | `fato_vendas_itens` | `dias_atraso_entrega`, `valor_frete` | `dim_tempo`, `dim_status_pedido` |
| **P09** | `fato_pagamentos_pedido` | `valor_pagamento`, `quantidade_parcelas` | `dim_tipo_pagamento`, `dim_tempo` |
| **P10** | `fato_vendas_itens` | `nota_avaliacao`, `dias_para_entrega` | `dim_status_pedido`, `dim_produto` |