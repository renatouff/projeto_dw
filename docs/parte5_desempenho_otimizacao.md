# PARTE 5 — ANÁLISE DE DESEMPENHO E OTIMIZAÇÃO NO POSTGRESQL 17

## 1. Metodologia de Medição e Estratégia de Otimização
Para avaliar o desempenho do esquema `dw` no PostgreSQL 17 de forma reproduzível (`etl/05_benchmark_performance.py`), utilizou-se o comando `EXPLAIN (ANALYZE, BUFFERS)` executando 5 rodadas por consulta antes e depois da aplicação do script `ddl/03_indexes_optimization.sql`, registrando a mediana e a média do tempo real de execução (*Execution Time*) e a quantidade de páginas de memória lidas (*Shared Buffers Hit*).

Foram implementadas duas frentes complementares de otimização para Data Warehousing:
1. **Indexação B-Tree e Índices de Cobertura (*Covering Indexes* com `INCLUDE`):** Criação de índices nas chaves estrangeiras das tabelas de fatos (`sk_tempo_compra`, `sk_produto`, `sk_cliente`, `sk_vendedor`, `sk_status_pedido`, `sk_tipo_pagamento`), atributos de filtragem dimensional (`ano, trimestre`, `categoria_pt`, `regiao_cliente, uf_cliente`) e índice composto `idx_fato_itens_status_tempo_entrega ON dw.fato_vendas_itens (sk_status_pedido, sk_tempo_compra) INCLUDE (dias_para_entrega, dias_atraso_entrega, valor_frete, nota_avaliacao)`, seguido de `ANALYZE` para atualizar as estatísticas do otimizador.
2. **Agregação ROLAP Materializada (`MATERIALIZED VIEW`):** Conforme fundamentado na Aula 03 (pág. 50 — *Agregações ROLAP armazenadas em tabelas relacionais*), criou-se a visão materializada `dw.mv_resumo_trimestral_vendas` para pré-computar o cubo `ROLLUP` trimestral e anual de vendas.

---

## 2. Resultados Reais Medidos (Antes vs. Depois)

| Caso de Teste | Mediana ANTES | Mediana DEPOIS | Buffers ANTES | Buffers DEPOIS | Ganho Medido | Mudança no Plano de Execução |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Caso 1:** Consulta seletiva de atrasos e satisfação (1º Trim/2018) | `32,910 ms` | **`1,889 ms`** | `3.020` | **`566`** | **-94,3% (17,42x mais rápido)** | `Seq Scan` na fato (`112.650` linhas) substituído por `Bitmap Index Scan` + `Index Only Scan` (`Heap Fetches: 0`) |
| **Caso 2:** Vendas de categoria de alto volume (`beleza_saude` — 9.670 itens) por Região | `77,385 ms` | `79,437 ms` | `42.749` | `42.234` | Estável (baixa seletividade na fato) | Em `dim_produto`, `Seq Scan` (`1.044` buffers) caiu para `Bitmap Index Scan` (`529` buffers); na fato, o otimizador manteve `Parallel Seq Scan` devido à baixa seletividade (~8,6% das linhas espalhadas nas páginas) |
| **Caso 3:** Relatório `ROLLUP` Trimestral e Anual (Consulta 01) | `211,727 ms` | **`0,025 ms`** | `3.019` | **`1`** | **-99,99% (8.469x mais rápido)** | `Seq Scan + MixedAggregate` em `112.650` linhas substituído por leitura direta da agregação ROLAP `mv_resumo_trimestral_vendas` |

---

## 3. Análise Técnica dos Planos de Execução (`EXPLAIN ANALYZE`)

1. **Eficácia de Índices Compostos e *Index Only Scan* em Consultas Seletivas (Caso 1):**
   - **Antes:** Sem índices nas chaves estrangeiras, o PostgreSQL executava `Seq Scan on fato_vendas_itens` lendo todas as `112.650` linhas (`3.002` blocos) e filtrava `dim_tempo` via `Seq Scan` (`Rows Removed by Filter: 1007`), totalizando `32,910 ms`.
   - **Depois:** O otimizador passou a usar `Bitmap Index Scan on idx_dim_tempo_ano_trimestre` (lendo apenas 2 blocos de índice) combinado com `Index Only Scan using idx_fato_itens_status_tempo_entrega on fato_vendas_itens`. Graças à cláusula `INCLUDE`, todas as métricas solicitadas estavam presentes nas folhas do índice (`Heap Fetches: 0`), reduzindo o I/O lógico em 81,3% (`3.020` para `566` buffers) e o tempo para `1,889 ms`.
2. **Comportamento do Otimizador em Consultas de Baixa Seletividade (Caso 2):**
   - Na dimensão `dim_produto`, o índice `idx_dim_produto_categoria_pt` reduziu pela metade os buffers lidos (`1.044` para `529`) e acelerou a filtragem da dimensão de `5,724 ms` para `1,190 ms`.
   - Entretanto, como a categoria líder `beleza_saude` possui `9.670` itens distribuídos ao longo de quase todas as `3.002` páginas físicas de `fato_vendas_itens`, o otimizador de custos escolheu manter o `Parallel Seq Scan` na tabela fato, evidenciando na prática por que consultas que agregam grandes frações da tabela fato não são resolvidas apenas com índices B-Tree secundários.
3. **Impacto das Agregações ROLAP Materializadas em Consultas Globais (Caso 3):**
   - Para relatórios executivos que varrem 100% da tabela fato com operadores `ROLLUP` (como a Consulta 01, que exigia `211,727 ms` e `MixedAggregate` sobre `112.650` linhas), a materialização da agregação ROLAP (`dw.mv_resumo_trimestral_vendas`) reduziu o custo de leitura de `3.019` páginas para **1 única página de memória**, entregando o resultado em `0,025 ms`.