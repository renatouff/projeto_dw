"""
DATA WAREHOUSE OLIST
Extrair os 9 arquivos CSV originais de data/raw/ e carregá-los no esquema staging sem transformações
"""

import os
import io
import csv
import time
import getpass
import pandas as pd
import psycopg2

# Caminho para a pasta data/raw relativo à raiz do projeto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")

# Mapeamento oficial dos 9 arquivos CSV para as 9 tabelas do esquema staging
ARQUIVOS_STAGING = [
    ("olist_orders_dataset.csv", "staging.stg_orders"),
    ("olist_order_items_dataset.csv", "staging.stg_order_items"),
    ("olist_order_payments_dataset.csv", "staging.stg_order_payments"),
    ("olist_order_reviews_dataset.csv", "staging.stg_order_reviews"),
    ("olist_customers_dataset.csv", "staging.stg_customers"),
    ("olist_sellers_dataset.csv", "staging.stg_sellers"),
    ("olist_products_dataset.csv", "staging.stg_products"),
    ("olist_geolocation_dataset.csv", "staging.stg_geolocation"),
    ("product_category_name_translation.csv", "staging.stg_category_translation"),
]


def obter_conexao():
    """Conecta ao PostgreSQL local (dw_olist) usando variáveis de ambiente ou prompt."""
    db_host = os.getenv("PGHOST", "localhost")
    db_port = os.getenv("PGPORT", "5432")
    db_name = os.getenv("PGDATABASE", "dw_olist")
    db_user = os.getenv("PGUSER", "postgres")
    db_pass = os.getenv("PGPASSWORD")

    if not db_pass:
        db_pass = getpass.getpass(f"Digite a senha do PostgreSQL para o usuário '{db_user}': ")

    return psycopg2.connect(
        host=db_host,
        port=db_port,
        dbname=db_name,
        user=db_user,
        password=db_pass
    )


def carregar_csv_para_staging(conn, nome_arquivo, tabela_destino):
    """Lê o CSV original sem transformar os dados e carrega na tabela staging."""
    caminho_csv = os.path.join(RAW_DIR, nome_arquivo)
    if not os.path.exists(caminho_csv):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_csv}")

    inicio = time.time()

    # Leitura bruta preservando os dados originais (dtype=str evita alterações de formato)
    df = pd.read_csv(caminho_csv, encoding="utf-8-sig", dtype=str, keep_default_na=False)
    qtd_linhas_csv = len(df)

    # Prepara buffer em memória para COPY de alta velocidade no PostgreSQL
    buffer = io.StringIO()
    df.to_csv(buffer, index=False, header=False, sep="\t", na_rep="\\N", quoting=csv.QUOTE_NONE, escapechar="\\")
    buffer.seek(0)

    with conn.cursor() as cur:
        cur.execute(f"TRUNCATE TABLE {tabela_destino};")
        sql_copy = f"""
            COPY {tabela_destino}
            FROM STDIN
            WITH (FORMAT CSV, HEADER TRUE, DELIMITER ',', NULL '', ENCODING 'UTF8');
        """
        with open(caminho_csv, mode="r", encoding="utf-8-sig") as f:
            cur.copy_expert(sql_copy, f)

        cur.execute(f"SELECT COUNT(*) FROM {tabela_destino};")
        qtd_banco = cur.fetchone()[0]

    conn.commit()
    duracao = time.time() - inicio
    print(f"[OK] {nome_arquivo:<42} -> {tabela_destino:<32} | CSV: {qtd_linhas_csv:>9} | Banco: {qtd_banco:>9} | {duracao:.2f}s")
    return qtd_linhas_csv, qtd_banco


def executar_extracao(conn=None):
    fechar_ao_final = False
    if conn is None:
        conn = obter_conexao()
        fechar_ao_final = True

    print("=" * 110)
    print("EXTRAÇÃO BRUTA DOS 9 ARQUIVOS CSV PARA O ESQUEMA STAGING")
    print("=" * 110)

    total_csv = 0
    total_banco = 0
    inicio_total = time.time()

    try:
        for arquivo, tabela in ARQUIVOS_STAGING:
            c_csv, c_db = carregar_csv_para_staging(conn, arquivo, tabela)
            total_csv += c_csv
            total_banco += c_db

        print("-" * 110)
        print(f"TOTAL GERAL CARREGADO EM STAGING: CSV = {total_csv} linhas | Banco = {total_banco} linhas | Tempo: {time.time() - inicio_total:.2f}s")
        print("=" * 110)
    finally:
        if fechar_ao_final:
            conn.close()


if __name__ == "__main__":
    executar_extracao()