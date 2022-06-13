from datetime import datetime
import awswrangler as wr
import datetime as dt
import logging
import boto3
import json
import os

logging.basicConfig()
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(getattr(logging, os.environ.get('LOG_LEVEL', 'DEBUG')))

STATE_MACHINE_TRUSTED = os.environ.get('STATE_MACHINE_TRUSTED')
STATE_MACHINE_REF = os.environ.get('STATE_MACHINE_REF')
GLUE_DB_TRUSTED_ECOMMERCE = os.environ.get('GLUE_DB_TRUSTED_ECOMMERCE')


def lambda_handler(event, context):
    LOGGER.debug("""
    ==============EventoStartStepFunctionsTrusted=============="""
                 + json.dumps(event) + """
    ===========================================================""")

    # 1° -> Setando parâmetros do evento do S3
    name_bucket = event['Records'][0]['s3']['bucket']['name']
    path_object = event['Records'][0]['s3']['object']['key']

    # 2° -> Preparando parâmetros para enviar para a StepFunction
    list_key_object = path_object.split("/")
    layer = list_key_object[0]
    location = list_key_object[1]
    owner = list_key_object[2]
    nome_objeto = list_key_object[3]
    source_path = "s3://" + name_bucket + "/" + layer + "/" + location + "/" + owner + "/" + nome_objeto + "/"
    target_path = "s3://" + name_bucket + "/TRUSTED/ECOMMERCE/" + nome_objeto + "/"

    # state == 1 --> Carga Full para tabela de ECOMMERCE.

    # 3° -> Setando nome dos databases do glue
    glue_db_trusted_ecommerce = GLUE_DB_TRUSTED_ECOMMERCE

    # 4° -> Print parâmetros
    parametros_log = """
    =======================================Parâmetros=======================================
    Nome do objeto: """ + nome_objeto + """
    Caminho da raw (origem): """ + source_path + """
    Caminho da ref (destino): """ + target_path + """
    Nome database de destino: """ + glue_db_trusted_intranet + """
    Chaves do objeto: """ + str(chaves_atualizacao) + """
    Nome da coluna que vai ser utilizada para particionar: """ + nome_col_particionada + """
    Nome da partição: """ + nome_particao + """
    Estado da carga: """ + str(state) + """
    ========================================================================================"""
    LOGGER.debug(parametros_log)

    # ===============================FIM DA DEFINIÇÃO DE PARÂMETROS===============================#

    # 5° -> Client da StepFunctions
    step_func = boto3.client('stepfunctions')

    # 7º -> Seta os caminhos de origem na camada Raw e destinho na camada Trusted #
    # (source_path & target_path) para cada caso e depois monta o payload         #
    # que será usado na execução das stepfunctions                                #

        # 7.1° -> Se for a tabela de Ecommerce entra no if e prepara
        # o Payload para ser executado pela stepfunction da StateMachineTrusted 
        if "ECOMMERCE" in nome_objeto:
            date = f"{datetime.today().strftime('%Y%m%d')}"
            source_path = f"s3://{name_bucket}/RAW/{location}/{date}/"
            target_path = f"s3://{name_bucket}/TRUSTED/{location}/"

            payload = {
                "name_bucket": name_bucket,
                "path_object": path_object,
                "nome_objeto": nome_objeto,
                "source_path": source_path,
                "target_path": target_path,
                "glue_db_target": glue_db_trusted_oneone,
                "state": 1
            }

    # 8° -> Start StepFunctions
    exec_name = f"{dt.datetime.today().strftime('%Y%m%d-%H%M%S%f')}-{nome_objeto.upper()}"

    execution = step_func.start_execution(
        stateMachineArn=STATE_MACHINE_TRUSTED,
        name=exec_name,
        input=json.dumps(payload)
    )

    imprime_result_start_stepfunction(exec_name, execution)

    LOGGER.info("Return: " + nome_objeto.upper())

    return nome_objeto.upper()

def exec_time():
    exec = f"{dt.datetime.today().strftime('%Y%m%d-%H%M%S%f')}"
    return exec

def imprime_result_start_stepfunction(exec_name, execution):
    step_func_log = """
    =======================================StepFunction=====================================
    Nome da execução na StepFunction: """ + exec_name + """
    Resultado da execução:
    """ + str(execution) + """
    ========================================================================================"""
    LOGGER.debug(step_func_log)


def retorna_state_completa_ou_inc(path_object):
    if path_object.split(".")[0][-4::] == "_INC":
        return 3
    else:
        return 2
