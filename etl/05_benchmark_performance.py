"""
DATA WAREHOUSE OLIST
Medir de forma reproduzível o desempenho e os planos de execução (EXPLAIN ANALYZE)
no PostgreSQL ANTES e DEPOIS da criação dos índices e agregações ROLAP (Etapa 5).
"""

import os
import re
import statistics
import psycopg2

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DDL_OPT_PATH = os.path.join(BASE_DIR, "ddl", "03_indexes_optimization.sql")
DOCS_DIR = os.path.join(BASE_DIR, "docs")


def obter_conexao():
    return psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        dbname=os.getenv("PGDATABASE", "dw_olist"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", "postgres")
    )


def remover_otimizacoes(conn):
    """Remove os índices de otimização e a materialized view para medir o baseline (ANTES)."""
    sql_drop = """
    DROP INDEX IF EXISTS dw.idx_fato_itens_sk_tempo_compra;
    DROP INDEX IF EXISTS dw.idx_fato_itens_sk_produto;
    DROP INDEX IF EXISTS dw.idx_fato_itens_sk_cliente;
    DROP INDEX IF EXISTS dw.idx_fato_itens_sk_vendedor;
    DROP INDEX IF EXISTS dw.idx_fato_itens_sk_status;
    DROP INDEX IF EXISTS dw.idx_fato_itens_status_tempo_entrega;
    DROP INDEX IF EXISTS dw.idx_fato_pag_sk_tempo_compra;
    DROP INDEX IF EXISTS dw.idx_fato_pag_sk_tipo_pagamento;
    DROP INDEX IF EXISTS dw.idx_fato_pag_sk_cliente;
    DROP INDEX IF EXISTS dw.idx_dim_cliente_regiao_uf;
    DROP INDEX IF EXISTS dw.idx_dim_cliente_unique_id;
    DROP INDEX IF EXISTS dw.idx_dim_produto_categoria_pt;
    DROP INDEX IF EXISTS dw.idx_dim_tempo_ano_trimestre;
    DROP MATERIALIZED VIEW IF EXISTS dw.mv_resumo_trimestral_vendas;
    ANALYZE dw.fato_vendas_itens;
    ANALYZE dw.fato_pagamentos_pedido;
    ANALYZE dw.dim_cliente;
    ANALYZE dw.dim_produto;
    ANALYZE dw.dim_tempo;
    ANALYZE dw.dim_status_pedido;
    """
    with conn.cursor() as cur:
        cur.execute(sql_drop)
    conn.commit()


def aplicar_otimizacoes(conn):
    """Executa o script ddl/03_indexes_optimization.sql."""
    with open(DDL_OPT_PATH, mode="r", encoding="utf-8") as f:
        sql_opt = f.read()
    with conn.cursor() as cur:
        cur.execute(sql_opt)
    conn.commit()


def medir_explain_analyze(conn, sql, rodadas=5):
    """
    Executa EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) múltiplas vezes,
    retorna a mediana do Execution Time (ms) e o texto do plano de execução.
    """
    tempos_exec = []
    plano_texto = ""

    with conn.cursor() as cur:
        for i in range(rodadas):
            cur.execute(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) {sql}")
            linhas = [row[0] for row in cur.fetchall()]
            texto = "\n".join(linhas)
            if i == rodadas - 1:
                plano_texto = texto

            match = re.search(r"Execution Time:\s*([\d\.]+)\s*ms", texto)
            if match:
                tempos_exec.append(float(match.group(1)))

    mediana_ms = statistics.median(tempos_exec) if tempos_exec else 0.0
    media_ms = statistics.mean(tempos_exec) if tempos_exec else 0.0
    return mediana_ms, media_ms, plano_texto


CASOS_TESTE = [
    (
        "Caso 1 — Consulta Analítica Seletiva de Atrasos Logísticos e Satisfação no 1º Trimestre de 2018",
        """
        SELECT
            s.status_pontualidade_entrega,
            COUNT(*) AS qtd_itens,
            ROUND(AVG(f.dias_para_entrega), 2) AS media_entrega,
            ROUND(AVG(f.dias_atraso_entrega), 2) AS media_atraso,
            ROUND(AVG(f.nota_avaliacao), 2) AS media_nota
        FROM dw.fato_vendas_itens f
        INNER JOIN dw.dim_status_pedido s ON f.sk_status_pedido = s.sk_status_pedido
        INNER JOIN dw.dim_tempo t ON f.sk_tempo_compra = t.sk_tempo
        WHERE s.status_pontualidade_entrega = 'Atrasado'
          AND t.ano = 2018 AND t.trimestre = 1
        GROUP BY s.status_pontualidade_entrega;
        """,
        None
    ),
    (
        "Caso 2 — Consulta de Vendas e Frete por Categoria Específica ('beleza_saude') e Região",
        """
        SELECT
            c.regiao_cliente,
            COUNT(*) AS qtd_itens,
            ROUND(SUM(f.valor_preco), 2) AS receita,
            ROUND(AVG(f.valor_frete), 2) AS frete_medio
        FROM dw.fato_vendas_itens f
        INNER JOIN dw.dim_produto p ON f.sk_produto = p.sk_produto
        INNER JOIN dw.dim_cliente c ON f.sk_cliente = c.sk_cliente
        WHERE p.categoria_pt = 'beleza_saude'
        GROUP BY c.regiao_cliente
        ORDER BY receita DESC;
        """,
        None
    ),
    (
        "Caso 3 — Consulta 01 (ROLLUP Trimestral/Anual na Fato Completa vs. Agregação ROLAP Materializada)",
        """
        SELECT
            COALESCE(t.ano::TEXT, 'TOTAL GERAL') AS ano,
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
        """,
        """
        SELECT ano, trimestre, qtd_itens_vendidos, receita_produtos, total_frete, faturamento_total
        FROM dw.mv_resumo_trimestral_vendas
        ORDER BY ano, num_trimestre NULLS LAST;
        """
    ),
]


def main():
    conn = obter_conexao()
    relatorio = []

    print("=" * 110)
    print("ETAPA 5 — BENCHMARK DE DESEMPENHO E OTIMIZAÇÃO (EXPLAIN ANALYZE ANTES vs. DEPOIS)")
    print("=" * 110)

    try:
        print("\n[1/3] Removendo índices de otimização para medir o BASELINE (ANTES)...")
        remover_otimizacoes(conn)

        resultados_antes = {}
        for titulo, sql_base, _ in CASOS_TESTE:
            med_ms, avg_ms, plano = medir_explain_analyze(conn, sql_base)
            resultados_antes[titulo] = (med_ms, avg_ms, plano)

        print("[2/3] Aplicando 'ddl/03_indexes_optimization.sql' (Índices B-Tree + Materialized View ROLAP)...")
        aplicar_otimizacoes(conn)

        print("[3/3] Medindo desempenho OTIMIZADO (DEPOIS) e comparando planos de execução...\n")

        for titulo, sql_base, sql_mv in CASOS_TESTE:
            med_antes, avg_antes, plano_antes = resultados_antes[titulo]
            sql_depois = sql_mv if sql_mv else sql_base
            med_depois, avg_depois, plano_depois = medir_explain_analyze(conn, sql_depois)

            reducao_pct = ((med_antes - med_depois) / med_antes * 100.0) if med_antes > 0 else 0.0
            speedup = (med_antes / med_depois) if med_depois > 0 else 1.0

            bloco = (
                f"{'=' * 110}\n"
                f">>> {titulo}\n"
                f"{'-' * 110}\n"
                f"  * Tempo de Execução ANTES (Sem Índices / Fato Bruta) : Mediana = {med_antes:>8.3f} ms | Média = {avg_antes:>8.3f} ms\n"
                f"  * Tempo de Execução DEPOIS (Com Índices / Otimizado) : Mediana = {med_depois:>8.3f} ms | Média = {avg_depois:>8.3f} ms\n"
                f"  * Ganho Medido                                       : Redução de {reducao_pct:.1f}% ({speedup:.2f}x mais rápido)\n\n"
                f"[PLANO DE EXECUÇÃO — ANTES]\n{plano_antes}\n\n"
                f"[PLANO DE EXECUÇÃO — DEPOIS]\n{plano_depois}\n"
            )
            print(bloco)
            relatorio.append(bloco)

        caminho_log = os.path.join(DOCS_DIR, "resultados_benchmark_parte5.txt")
        with open(caminho_log, mode="w", encoding="utf-8") as f:
            f.write("\n".join(relatorio))

        print("=" * 110)
        print("[SUCESSO] Benchmark concluído! Índices ativos no DW e log salvo em 'docs/resultados_benchmark_parte5.txt'.")
        print("=" * 110)
    finally:
        conn.close()


if __name__ == "__main__":
    main()