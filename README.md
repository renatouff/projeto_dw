# Data Warehouse Olist — Projeto Prático Extra (PostgreSQL 17 + Python)

Implementação completa de um Data Warehouse dimensional em Esquema Estrela (*Star Schema*) sobre o *Brazilian E-Commerce Public Dataset by Olist*, utilizando **PostgreSQL 17** e **Python 3.13**.

---

## 1. Estrutura do Repositório

```text
projeto_dw/
├── data/
│   └── raw/                                  # 9 arquivos CSV originais do dataset Olist
├── ddl/
│   ├── 01_create_staging.sql                 # Criação do esquema staging e das 9 tabelas brutas
│   ├── 02_create_dw.sql                      # Criação do esquema dw (6 dimensões, membros -1, dim_tempo e 2 fatos)
│   └── 03_indexes_optimization.sql           # Criação de índices B-Tree, Covering Index e Materialized View ROLAP
├── etl/
│   ├── 01_extract_staging.py                 # Extração bruta via COPY dos 9 CSVs para o esquema staging
│   ├── 02_transform_load_dw.py               # Auditoria das 10 regras de limpeza, Lookup e Carga Inicial/Incremental
│   ├── 03_validate_dw.py                     # Testes automatizados de idempotência (1x vs 2x) e integridade referencial
│   ├── 04_run_queries.py                     # Geração e execução das 10 consultas analíticas SQL
│   ├── 05_benchmark_performance.py           # Benchmark EXPLAIN (ANALYZE, BUFFERS) antes e depois dos índices
│   └── run_pipeline.py                       # Orquestrador de comando único (executa todo o pipeline de ponta a ponta)
├── queries/
│   └── consulta_01.sql ... consulta_10.sql   # As 10 consultas analíticas em SQL (uma por arquivo)
├── docs/
│   ├── parte1_modelagem_dimensional.md       # Levantamento das 10 perguntas, fatos, dimensões e modelo estrela
│   ├── parte2_dicionario_dados_dw.md         # Dicionário de dados completo do esquema dw
│   ├── parte4_consultas_analiticas.md        # Resultados reais e interpretações das 10 consultas
│   ├── parte5_desempenho_otimizacao.md       # Análise de desempenho e planos de execução EXPLAIN ANALYZE
│   ├── resultados_consultas_parte4.txt       # Log de saída das 10 consultas executadas no banco
│   └── resultados_benchmark_parte5.txt       # Log completo dos planos EXPLAIN ANALYZE antes e depois
└── README.md
```

---

## 2. Pré-requisitos e Configuração do Ambiente

1. **Banco de Dados:** PostgreSQL 17 rodando localmente (`localhost:5432`) com um banco criado com o nome `dw_olist`:
   ```sql
   CREATE DATABASE dw_olist;
   ```
2. **Pacotes Python:**
   ```powershell
   python -m pip install pandas psycopg2-binary sqlalchemy
   ```
3. **Variáveis de Conexão (Valores Padrão):**
   - `PGHOST=localhost` | `PGPORT=5432` | `PGDATABASE=dw_olist` | `PGUSER=SEU_USUARIO_LOCAL` | `PGPASSWORD=SUA_SENHA`

---

## 3. Execução do Pipeline Completo por Comando Único

Para executar todo o pipeline (recriação dos esquemas `staging` e `dw`, extração dos 9 arquivos CSV com `1.550.922` linhas, limpeza e transformação com auditoria, carga inicial até `31/12/2017`, teste de idempotência, carga incremental de `2018`, segundo teste de idempotência, criação de índices e execução das 10 consultas analíticas), execute na raiz do projeto:

```powershell
python etl/run_pipeline.py
```

### Comandos Individuais (Opcional)
- **Apenas Extração (`staging`):** `python etl/01_extract_staging.py`
- **Apenas Carga Inicial (`<= 31/12/2017`):** `python etl/02_transform_load_dw.py --modo inicial`
- **Apenas Carga Incremental (`> 31/12/2017`):** `python etl/02_transform_load_dw.py --modo incremental`
- **Validação de Idempotência e Integridade:** `python etl/03_validate_dw.py`
- **Execução das 10 Consultas Analíticas:** `python etl/04_run_queries.py`
- **Benchmark de Desempenho (`EXPLAIN ANALYZE`):** `python etl/05_benchmark_performance.py`