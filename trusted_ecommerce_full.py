import awswrangler as wr
import logging
import json
import os

logging.basicConfig()
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(getattr(logging, os.environ.get('LOG_LEVEL', 'DEBUG')))


def lambda_handler(event, context):
    LOGGER.debug("""
    =========EventoTrustedEcommerceFull=========="""
                 + json.dumps(event) + """
    =================================================""")

    target_path = event['target_path']
    source_path = event['source_path']
    nome_objeto = event['nome_objeto']
    glue_db_oneone = event['glue_db_target']

    nome_objeto = os.path.splitext(nome_objeto)[0]

    LOGGER.debug("Executando leitura...")
    df = wr.s3.read_csv(source_path + nome_objeto, sep=';', encoding='utf-8')
    LOGGER.debug("Leitura concluída!")

    LOGGER.debug("Executando conversão...")
    wr.s3.to_parquet(df=df, path=target_path, dataset=True, mode="overwrite")
    LOGGER.debug("Conversão concluída!")

    # Recupera os comentários da tabela e caso não existir cria os comentários vazios.
    try:
        desc = wr.catalog.get_table_description(database=glue_db_ecommerce, table=nome_objeto)
        comments = wr.catalog.get_columns_comments(database=glue_db_ecommerce, table=nome_objeto)
    except:
        desc = "Tabela sem descrição"
        comments = {}
        for c in df.columns:
            comments[c] = "N/A"
    LOGGER.debug("Lógica dos comentários executada com sucesso")

     # Criar, manter, sobrescrever o objeto no catálogo do glue ou adicionar nova coluna no catálogo do glue.
    try:
        # Cria ou mantém catalogo do glue ou adiciona nova coluna se existir (mode==overwrite).
        wr.s3.store_parquet_metadata(
            path=target_path,
            database=glue_db_oneone,
            table=nome_objeto,
            dataset=True,
            mode="overwrite",
            catalog_versioning=True,
            compression='snappy',
            description=desc,
            columns_comments=comments
        )
        LOGGER.debug("Catálogo criado, mantido ou adicionado novas colunas com sucesso (mode==overwrite)")
    except:
        LOGGER.debug("O catálogo não foi alterado, verifique se há colunas vazias na tabela " + nome_objeto)
        pass

    return 0