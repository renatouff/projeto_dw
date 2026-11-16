"""
DATA WAREHOUSE OLIST
Testar idempotência da carga inicial, executar a carga incremental (pós-2017),
testar idempotência da carga incremental e validar integridade do DW.
"""

import importlib.util
import os
import psycopg2

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ETL_02_PATH = os.path.join(BASE_DIR, "etl", "02_transform_load_dw.py")

spec = importlib.util.spec_from_file_location("transform_load_dw", ETL_02_PATH)
mod_etl02 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod_etl02)


def contar(conn, tabela):
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {tabela};")
        return cur.fetchone()[0]


def executar_validacao_completa(conn=None):
    fechar = False
    if conn is None:
        conn = mod_etl02.obter_conexao()
        fechar = True

    print("=" * 110)
    print("TESTE DE IDEMPOTÊNCIA, CARGA INCREMENTAL E VALIDAÇÃO DE INTEGRIDADE DO DW")
    print("=" * 110)

    try:
        # 1. Verifica estado atual (após 1ª Carga Inicial) e reexecuta Carga Inicial (Teste de Idempotência 1)
        itens_antes_reexec_ini = contar(conn, "dw.fato_vendas_itens")
        pag_antes_reexec_ini = contar(conn, "dw.fato_pagamentos_pedido")

        print(f"\n[TESTE 1] Reexecutando CARGA INICIAL para testar idempotência...")
        mod_etl02.carregar_dimensoes(conn)
        mod_etl02.carregar_fatos(conn, modo="inicial")

        itens_depois_reexec_ini = contar(conn, "dw.fato_vendas_itens")
        pag_depois_reexec_ini = contar(conn, "dw.fato_pagamentos_pedido")

        print(f"  -> fato_vendas_itens (Inicial 1x vs 2x)    : {itens_antes_reexec_ini} vs {itens_depois_reexec_ini}")
        print(f"  -> fato_pagamentos_pedido (Inicial 1x vs 2x): {pag_antes_reexec_ini} vs {pag_depois_reexec_ini}")
        assert itens_antes_reexec_ini == itens_depois_reexec_ini, "ERRO: Duplicação na Carga Inicial de itens!"
        assert pag_antes_reexec_ini == pag_depois_reexec_ini, "ERRO: Duplicação na Carga Inicial de pagamentos!"
        print("  [APROVADO] Executar a Carga Inicial duas vezes não duplicou nenhuma linha!")

        # 2. Executa a Carga Incremental (pedidos após 31/12/2017)
        print(f"\n[TESTE 2] Executando CARGA INCREMENTAL (Pedidos de 2018)...")
        mod_etl02.carregar_fatos(conn, modo="incremental")

        itens_pos_inc_1 = contar(conn, "dw.fato_vendas_itens")
        pag_pos_inc_1 = contar(conn, "dw.fato_pagamentos_pedido")
        print(f"  -> fato_vendas_itens após Carga Incremental (1ª execução)    : {itens_pos_inc_1} (+{itens_pos_inc_1 - itens_depois_reexec_ini} itens de 2018)")
        print(f"  -> fato_pagamentos_pedido após Carga Incremental (1ª execução): {pag_pos_inc_1} (+{pag_pos_inc_1 - pag_depois_reexec_ini} pagamentos de 2018)")

        # 3. Reexecuta a Carga Incremental uma 2ª vez (Teste de Idempotência 2)
        print(f"\n[TESTE 3] Reexecutando CARGA INCREMENTAL uma 2ª vez para testar idempotência...")
        mod_etl02.carregar_dimensoes(conn)
        mod_etl02.carregar_fatos(conn, modo="incremental")

        itens_pos_inc_2 = contar(conn, "dw.fato_vendas_itens")
        pag_pos_inc_2 = contar(conn, "dw.fato_pagamentos_pedido")
        print(f"  -> fato_vendas_itens (Incremental 1x vs 2x)    : {itens_pos_inc_1} vs {itens_pos_inc_2}")
        print(f"  -> fato_pagamentos_pedido (Incremental 1x vs 2x): {pag_pos_inc_1} vs {pag_pos_inc_2}")
        assert itens_pos_inc_1 == itens_pos_inc_2 == 112650, "ERRO: Contagem final de itens divergente!"
        assert pag_pos_inc_1 == pag_pos_inc_2 == 103886, "ERRO: Contagem final de pagamentos divergente!"
        print("  [APROVADO] Executar a Carga Incremental duas vezes não duplicou nenhuma linha!")

        # 4. Auditoria de Integridade Referencial, Ausência de FKs Nulas e Uso de Membros Desconhecidos (-1)
        print(f"\n[TESTE 4] Auditoria de Integridade Referencial, Grãos e Membros Desconhecidos (-1):")
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE sk_tempo_compra IS NULL OR sk_tempo_entrega IS NULL OR sk_tempo_estimada IS NULL
                                        OR sk_cliente IS NULL OR sk_vendedor IS NULL OR sk_produto IS NULL OR sk_status_pedido IS NULL) AS fks_nulas_itens,
                    COUNT(*) FILTER (WHERE sk_tempo_entrega = -1) AS itens_sem_data_entrega_mapeados_menos1,
                    COUNT(*) - COUNT(DISTINCT (nk_order_id, nk_order_item_id)) AS duplicatas_grao_itens,
                    ROUND(SUM(valor_preco), 2) AS soma_preco_dw,
                    ROUND(SUM(valor_frete), 2) AS soma_frete_dw
                FROM dw.fato_vendas_itens;
            """)
            fks_nulas_it, sem_entrega_it, dup_it, soma_preco, soma_frete = cur.fetchone()

            cur.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE sk_tempo_compra IS NULL OR sk_cliente IS NULL
                                        OR sk_status_pedido IS NULL OR sk_tipo_pagamento IS NULL) AS fks_nulas_pag,
                    COUNT(*) - COUNT(DISTINCT (nk_order_id, nk_payment_sequential)) AS duplicatas_grao_pag,
                    ROUND(SUM(valor_pagamento), 2) AS soma_pagamentos_dw
                FROM dw.fato_pagamentos_pedido;
            """)
            fks_nulas_pg, dup_pg, soma_pag = cur.fetchone()

            print(f"  * Chaves estrangeiras nulas em fato_vendas_itens               : {fks_nulas_it}")
            print(f"  * Chaves estrangeiras nulas em fato_pagamentos_pedido          : {fks_nulas_pg}")
            print(f"  * Duplicatas de grão em fato_vendas_itens                      : {dup_it}")
            print(f"  * Duplicatas de grão em fato_pagamentos_pedido                 : {dup_pg}")
            print(f"  * Itens sem data de entrega mapeados para sk_tempo_entrega = -1: {sem_entrega_it}")
            print(f"  * Soma total de valor_preco em fato_vendas_itens               : R$ {soma_preco:,.2f}")
            print(f"  * Soma total de valor_frete em fato_vendas_itens               : R$ {soma_frete:,.2f}")
            print(f"  * Soma total de valor_pagamento em fato_pagamentos_pedido      : R$ {soma_pag:,.2f}")

            assert fks_nulas_it == 0 and fks_nulas_pg == 0, "ERRO: Existem FKs nulas!"
            assert dup_it == 0 and dup_pg == 0, "ERRO: Existem duplicatas no grão!"

        mod_etl02.exibir_resumo_dw(conn, titulo="RESUMO FINAL DO DW (CARGA INICIAL + INCREMENTAL VALIDADAS)")
        print("\n[SUCESSO TOTAL] Todos os requisitos da Parte 3 (ETL) foram validados com 100% de precisão!")
    finally:
        if fechar:
            conn.close()


if __name__ == "__main__":
    executar_validacao_completa()