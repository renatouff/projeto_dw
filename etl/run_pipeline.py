"""
DATA WAREHOUSE OLIST
Executar todo o pipeline de ponta a ponta (DDL -> Extração Staging ->
Transformação e Carga Inicial -> Carga Incremental -> Validações de Idempotência ->
Otimização de Índices -> Execução das 10 Consultas Analíticas)
por um único comando documentado no README: python etl/run_pipeline.py
"""

import os
import time
import importlib.util

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def carregar_modulo(nome_modulo, caminho_relativo):
    caminho = os.path.join(BASE_DIR, *caminho_relativo.split("/"))
    spec = importlib.util.spec_from_file_location(nome_modulo, caminho)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def executar_script_sql(conn, caminho_relativo):
    caminho = os.path.join(BASE_DIR, *caminho_relativo.split("/"))
    with open(caminho, mode="r", encoding="utf-8") as f:
        sql = f.read()
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    print(f"[OK] Script DDL executado: {caminho_relativo}")


def main():
    inicio_global = time.time()
    print("#" * 110)
    print(" INICIANDO PIPELINE COMPLETO DO DATA WAREHOUSE OLIST (COMANDO ÚNICO)")
    print("#" * 110)

    mod_01 = carregar_modulo("extract_staging", "etl/01_extract_staging.py")
    mod_02 = carregar_modulo("transform_load_dw", "etl/02_transform_load_dw.py")
    mod_03 = carregar_modulo("validate_dw", "etl/03_validate_dw.py")
    mod_04 = carregar_modulo("run_queries", "etl/04_run_queries.py")

    conn = mod_02.obter_conexao()
    try:
        print("\n>>> PASSO 1: Recriando esquemas e tabelas (DDL staging e dw)...")
        executar_script_sql(conn, "ddl/01_create_staging.sql")
        executar_script_sql(conn, "ddl/02_create_dw.sql")

        print("\n>>> PASSO 2: Extraindo os 9 arquivos CSV brutos para o esquema staging...")
        mod_01.executar_extracao(conn)

        print("\n>>> PASSO 3: Limpeza, Transformação e Carga Inicial (Pedidos até 31/12/2017)...")
        mod_02.auditar_regras_limpeza(conn)
        mod_02.carregar_dimensoes(conn)
        mod_02.carregar_fatos(conn, modo="inicial")
        mod_02.exibir_resumo_dw(conn, titulo="RESUMO APÓS CARGA INICIAL (ATÉ 31/12/2017)")

        print("\n>>> PASSO 4: Validação de Idempotência, Carga Incremental (2018) e Auditoria Final...")
        mod_03.executar_validacao_completa(conn)

        print("\n>>> PASSO 5: Aplicando Índices B-Tree e Agregação ROLAP Materializada (Otimização)...")
        executar_script_sql(conn, "ddl/03_indexes_optimization.sql")

        print("\n>>> PASSO 6: Executando as 10 Consultas Analíticas em SQL...")
        mod_04.main()

        print("\n" + "#" * 110)
        print(f" PIPELINE COMPLETO FINALIZADO COM SUCESSO EM {time.time() - inicio_global:.2f}s!")
        print("#" * 110)
    finally:
        conn.close()


if __name__ == "__main__":
    main()