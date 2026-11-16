"""
DATA WAREHOUSE OLIST
Criar os 10 arquivos SQL na pasta queries/ (consulta_01.sql a consulta_10.sql),
executá-los no banco PostgreSQL dw_olist e exibir os resultados reais (Etapa 4).
"""

import os
import psycopg2
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUERIES_DIR = os.path.join(BASE_DIR, "queries")
DOCS_DIR = os.path.join(BASE_DIR, "docs")


def obter_conexao():
    return psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        dbname=os.getenv("PGDATABASE", "dw_olist"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", "postgres")
    )


def executar_consulta_df(conn, sql):
    """Executa uma consulta SQL e retorna um DataFrame pandas sem gerar warnings."""
    with conn.cursor() as cur:
        cur.execute(sql)
        colunas = [desc[0] for desc in cur.description]
        dados = cur.fetchall()
    return pd.DataFrame(dados, columns=colunas)


CONSULTAS = [
    (
        "consulta_01.sql",
        "Pergunta 01: Qual é a evolução anual e trimestral da receita de produtos, do valor total de frete e do faturamento bruto dos itens vendidos, incluindo subtotais por ano e total geral (ROLLUP)?",
        """-- ============================================================================
-- Arquivo: queries/consulta_01.sql
-- Pergunta 01: Qual é a evolução anual e trimestral da receita de produtos,
--              do valor total de frete e do faturamento bruto dos itens vendidos,
--              incluindo subtotais por ano e total geral (ROLLUP)?
-- ============================================================================
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
"""
    ),
    (
        "consulta_02.sql",
        "Pergunta 02: Quais são as 10 categorias de produtos (em português e inglês) com maior receita acumulada de vendas, qual o volume de itens vendidos e o ticket médio por item em cada categoria?",
        """-- ============================================================================
-- Arquivo: queries/consulta_02.sql
-- Pergunta 02: Quais são as 10 categorias de produtos (em português e inglês)
--              com maior receita acumulada de vendas, qual o volume de itens
--              vendidos e o ticket médio por item em cada categoria?
-- ============================================================================
SELECT
    p.categoria_pt,
    p.categoria_en,
    SUM(f.quantidade_item) AS qtd_itens_vendidos,
    COUNT(DISTINCT f.nk_order_id) AS qtd_pedidos,
    ROUND(SUM(f.valor_preco), 2) AS receita_produtos,
    ROUND(AVG(f.valor_preco), 2) AS ticket_medio_item,
    ROUND(SUM(f.valor_total_item), 2) AS faturamento_com_frete
FROM dw.fato_vendas_itens f
INNER JOIN dw.dim_produto p ON f.sk_produto = p.sk_produto
GROUP BY p.categoria_pt, p.categoria_en
ORDER BY receita_produtos DESC
LIMIT 10;
"""
    ),
    (
        "consulta_03.sql",
        "Pergunta 03: Como se distribuem a receita de produtos e o gasto com frete por Região e UF de destino do cliente, considerando os subtotais por Região e o total geral (GROUPING SETS)?",
        """-- ============================================================================
-- Arquivo: queries/consulta_03.sql
-- Pergunta 03: Como se distribuem a receita de produtos e o gasto com frete por
--              Região e UF de destino do cliente, considerando os subtotais por
--              Região e o total geral (GROUPING SETS)?
-- ============================================================================
SELECT
    COALESCE(c.regiao_cliente, 'TOTAL BRASIL') AS regiao,
    COALESCE(c.uf_cliente, 'Subtotal Regiao') AS uf,
    SUM(f.quantidade_item) AS qtd_itens,
    ROUND(SUM(f.valor_preco), 2) AS receita_produtos,
    ROUND(SUM(f.valor_frete), 2) AS total_frete,
    ROUND(AVG(f.valor_frete), 2) AS frete_medio_item,
    ROUND(100.0 * SUM(f.valor_frete) / NULLIF(SUM(f.valor_total_item), 0), 2) AS pct_frete_sobre_total
FROM dw.fato_vendas_itens f
INNER JOIN dw.dim_cliente c ON f.sk_cliente = c.sk_cliente
GROUP BY GROUPING SETS (
    (c.regiao_cliente, c.uf_cliente),
    (c.regiao_cliente),
    ()
)
ORDER BY receita_produtos DESC;
"""
    ),
    (
        "consulta_04.sql",
        "Pergunta 04: Quais são os 10 vendedores com maior receita acumulada de produtos, quantos itens e pedidos atenderam e qual a sua localização (cidade, UF e região)?",
        """-- ============================================================================
-- Arquivo: queries/consulta_04.sql
-- Pergunta 04: Quais são os 10 vendedores com maior receita acumulada de produtos,
--              quantos itens e pedidos atenderam e qual a sua localização?
-- ============================================================================
SELECT
    v.nk_seller_id AS seller_id,
    v.cidade_vendedor,
    v.uf_vendedor,
    v.regiao_vendedor,
    COUNT(DISTINCT f.nk_order_id) AS qtd_pedidos_atendidos,
    SUM(f.quantidade_item) AS qtd_itens_vendidos,
    ROUND(SUM(f.valor_preco), 2) AS receita_produtos,
    ROUND(AVG(f.valor_preco), 2) AS preco_medio_item
FROM dw.fato_vendas_itens f
INNER JOIN dw.dim_vendedor v ON f.sk_vendedor = v.sk_vendedor
GROUP BY v.nk_seller_id, v.cidade_vendedor, v.uf_vendedor, v.regiao_vendedor
ORDER BY receita_produtos DESC
LIMIT 10;
"""
    ),
    (
        "consulta_05.sql",
        "Pergunta 05: Qual é o faturamento total, o volume de itens vendidos e a média de faturamento por dia em dias úteis em comparação com finais de semana e feriados nacionais?",
        """-- ============================================================================
-- Arquivo: queries/consulta_05.sql
-- Pergunta 05: Qual é o faturamento total, o volume de itens vendidos e a média
--              de faturamento por dia com vendas em dias úteis, finais de semana
--              e feriados nacionais?
-- ============================================================================
SELECT
    CASE
        WHEN t.eh_feriado_nacional = 'Sim' THEN 'Feriado Nacional'
        WHEN t.eh_fim_de_semana = 'Sim' THEN 'Fim de Semana'
        ELSE 'Dia Util'
    END AS tipo_dia_calendario,
    COUNT(DISTINCT t.sk_tempo) AS qtd_dias_com_vendas,
    COUNT(DISTINCT f.nk_order_id) AS qtd_pedidos,
    SUM(f.quantidade_item) AS qtd_itens_vendidos,
    ROUND(SUM(f.valor_total_item), 2) AS faturamento_total,
    ROUND(SUM(f.valor_total_item) / NULLIF(COUNT(DISTINCT t.sk_tempo), 0), 2) AS media_faturamento_por_dia
FROM dw.fato_vendas_itens f
INNER JOIN dw.dim_tempo t ON f.sk_tempo_compra = t.sk_tempo
GROUP BY
    CASE
        WHEN t.eh_feriado_nacional = 'Sim' THEN 'Feriado Nacional'
        WHEN t.eh_fim_de_semana = 'Sim' THEN 'Fim de Semana'
        ELSE 'Dia Util'
    END
ORDER BY media_faturamento_por_dia DESC;
"""
    ),
    (
        "consulta_06.sql",
        "Pergunta 06: Quantos clientes reais (customer_unique_id) realizaram mais de um pedido na plataforma e qual é o valor médio gasto por cliente recorrente em comparação aos clientes de compra única?",
        """-- ============================================================================
-- Arquivo: queries/consulta_06.sql
-- Pergunta 06: Quantos clientes reais (customer_unique_id) realizaram mais de um
--              pedido na plataforma e qual é o valor médio gasto por cliente
--              recorrente em comparação aos clientes de compra única?
-- ============================================================================
WITH gastos_por_cliente AS (
    SELECT
        c.customer_unique_id,
        COUNT(DISTINCT f.nk_order_id) AS qtd_pedidos_cliente,
        SUM(f.quantidade_item) AS qtd_itens_comprados,
        SUM(f.valor_total_item) AS gasto_total_cliente
    FROM dw.fato_vendas_itens f
    INNER JOIN dw.dim_cliente c ON f.sk_cliente = c.sk_cliente
    GROUP BY c.customer_unique_id
)
SELECT
    CASE
        WHEN qtd_pedidos_cliente > 1 THEN 'Cliente Recorrente (2+ pedidos)'
        ELSE 'Cliente Compra Unica (1 pedido)'
    END AS perfil_fidelidade,
    COUNT(*) AS qtd_clientes_unicos,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_clientes,
    SUM(qtd_pedidos_cliente) AS total_pedidos,
    ROUND(SUM(gasto_total_cliente), 2) AS faturamento_total,
    ROUND(AVG(gasto_total_cliente), 2) AS gasto_medio_por_cliente
FROM gastos_por_cliente
GROUP BY
    CASE
        WHEN qtd_pedidos_cliente > 1 THEN 'Cliente Recorrente (2+ pedidos)'
        ELSE 'Cliente Compra Unica (1 pedido)'
    END
ORDER BY qtd_clientes_unicos DESC;
"""
    ),
    (
        "consulta_07.sql",
        "Pergunta 07: Qual é o tempo médio real de entrega (em dias) e a diferença média em relação ao prazo estimado por Região de destino do cliente nos pedidos entregues?",
        """-- ============================================================================
-- Arquivo: queries/consulta_07.sql
-- Pergunta 07: Qual é o tempo médio real de entrega (em dias) e a diferença
--              média em relação ao prazo estimado por Região de destino do
--              cliente nos pedidos entregues?
-- ============================================================================
SELECT
    c.regiao_cliente,
    COUNT(*) AS qtd_itens_entregues,
    ROUND(AVG(f.dias_para_entrega), 2) AS media_dias_entrega_real,
    ROUND(AVG(f.dias_atraso_entrega), 2) AS media_diferenca_estimativa_dias,
    SUM(CASE WHEN s.status_pontualidade_entrega = 'Atrasado' THEN 1 ELSE 0 END) AS qtd_itens_atrasados,
    ROUND(
        100.0 * SUM(CASE WHEN s.status_pontualidade_entrega = 'Atrasado' THEN 1 ELSE 0 END) / COUNT(*),
        2
    ) AS taxa_atraso_pct
FROM dw.fato_vendas_itens f
INNER JOIN dw.dim_cliente c ON f.sk_cliente = c.sk_cliente
INNER JOIN dw.dim_status_pedido s ON f.sk_status_pedido = s.sk_status_pedido
WHERE s.status_pedido_original = 'delivered'
  AND f.dias_para_entrega IS NOT NULL
GROUP BY c.regiao_cliente
ORDER BY media_dias_entrega_real DESC;
"""
    ),
    (
        "consulta_08.sql",
        "Pergunta 08: Qual é o percentual trimestral de itens entregues com atraso (entregues após a data estimada) e como se comporta o valor médio de frete nesses períodos?",
        """-- ============================================================================
-- Arquivo: queries/consulta_08.sql
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
"""
    ),
    (
        "consulta_09.sql",
        "Pergunta 09: Qual é a participação de cada meio de pagamento no valor total transacionado, na quantidade de transações e qual é o número médio de parcelas contratadas?",
        """-- ============================================================================
-- Arquivo: queries/consulta_09.sql
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
"""
    ),
    (
        "consulta_10.sql",
        "Pergunta 10: Qual é o impacto da pontualidade logística de entrega (No Prazo vs. Atrasado vs. Não Entregue) sobre a nota média de avaliação dos clientes (nota_avaliacao) e o tempo médio de espera?",
        """-- ============================================================================
-- Arquivo: queries/consulta_10.sql
-- Pergunta 10: Qual é o impacto da pontualidade logística de entrega
--              (No Prazo, Atrasado, Nao Entregue) sobre a nota média de
--              avaliação dos clientes e o tempo médio de entrega?
-- ============================================================================
SELECT
    s.status_pontualidade_entrega,
    COUNT(DISTINCT f.nk_order_id) AS qtd_pedidos,
    COUNT(f.nota_avaliacao) AS qtd_itens_avaliados,
    ROUND(AVG(f.nota_avaliacao), 2) AS nota_media_avaliacao,
    ROUND(AVG(f.dias_para_entrega), 2) AS media_dias_entrega,
    ROUND(AVG(f.dias_atraso_entrega), 2) AS media_dias_atraso
FROM dw.fato_vendas_itens f
INNER JOIN dw.dim_status_pedido s ON f.sk_status_pedido = s.sk_status_pedido
GROUP BY s.status_pontualidade_entrega
ORDER BY nota_media_avaliacao DESC;
"""
    ),
]


def main():
    os.makedirs(QUERIES_DIR, exist_ok=True)
    os.makedirs(DOCS_DIR, exist_ok=True)

    conn = obter_conexao()
    linhas_relatorio = []

    print("=" * 110)
    print("ETAPA 4 — CRIAÇÃO E EXECUÇÃO DAS 10 CONSULTAS ANALÍTICAS EM SQL NO BANCO DW_OLIST")
    print("=" * 110)

    try:
        for nome_arq, pergunta, sql in CONSULTAS:
            caminho_sql = os.path.join(QUERIES_DIR, nome_arq)
            with open(caminho_sql, mode="w", encoding="utf-8") as f:
                f.write(sql)

            df = executar_consulta_df(conn, sql)
            bloco = f"\n>>> ARQUIVO: queries/{nome_arq}\n{pergunta}\n" + "-" * 110 + "\n" + df.to_string(index=False) + "\n"
            print(bloco)
            linhas_relatorio.append(bloco)

        caminho_txt = os.path.join(DOCS_DIR, "resultados_consultas_parte4.txt")
        with open(caminho_txt, mode="w", encoding="utf-8") as f:
            f.write("\n".join(linhas_relatorio))

        print("=" * 110)
        print("[SUCESSO] Os 10 arquivos .sql foram salvos em 'queries/' e os resultados em 'docs/resultados_consultas_parte4.txt'!")
        print("=" * 110)
    finally:
        conn.close()


if __name__ == "__main__":
    main()