from office365.runtime.auth.user_credential import UserCredential
from office365.sharepoint.files.file import File
from datetime import datetime, date
import logging
import base64
import boto3
import json
import os
import requests

logging.basicConfig()
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(getattr(logging, os.environ.get('LOG_LEVEL', 'DEBUG')))

NAME_BUCKET = os.environ.get('NAME_BUCKET')
NAME_REGION = os.environ.get('NAME_REGION')

def lambda_handler(event, context):
    LOGGER.debug("""
    =============EventoIngestaoEcommerce=============="""
                 + json.dumps(event) + """
    ======================================================""")

    # Especifica o nome do arquivo a ser salvo e o local
    nome_arquivo = "custormers.csv"
    local_file = f"/wamp64/tmp/{nome_arquivo}"

    # Recupera as variáveis de acesso necessárias pelo secrets
    secret = json.loads(get_secret())

    # Atribui os valores recuperados às variáves necessárias
    user = secret['API_USER']
    password = secret['API_PASSWORD']
    credentials = UserCredential(user, password)

    # Tenta fazer o download do arquivo, se não conseguir retorna um erro e finaliza o processo
    try:
        download_arquivo(credentials, local_file)
    except:
        LOGGER.debug('Erro ao fazer o download do arquivo. Verifique se o arquivo da data atual está na Pasta Informada.')
        return 0
    
    # Faz upload do arquivo no s3
    upload_s3(local_file, nome_arquivo)

    return 0


def get_secret():

    secret_name = "Ingestao_Ecommerce"
    region_name = NAME_REGION

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    get_secret_value_response = client.get_secret_value(
        SecretId=secret_name
    )
    if 'SecretString' in get_secret_value_response:
        secret = get_secret_value_response['SecretString']
        return secret
    else:
        decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
        return decoded_binary_secret


def download_arquivo(credentials, local_file):
    LOGGER.debug("Início do processo de download")

    # Url do arquivo Localmente
    today = date.today()
    periodo = today.strftime("%d%m%Y")
    abs_file_url = f"C:/wamp64/tmp/custormers.csv" # Estamos colocando como exemplo um arquivo local.
    file_name = os.path.basename(abs_file_url)

    parametros_log = """
    =======================================Parâmetros=======================================
    Url de download: """ + abs_file_url + """
    Arquivo de download:: """ + file_name + """
    ========================================================================================"""

    LOGGER.debug(parametros_log)

    # Persiste o arquivo na lambda para ser baixado
    with open(local_file, 'wb') as fh:
        fh = File.from_url(abs_file_url).with_credentials(credentials).download(fh).execute_query()
    LOGGER.debug("Download realizado na pasta: " + local_file)


def upload_s3(local_file, nome_arquivo):
    LOGGER.debug("Início do processo de upload")
    # Cria o recurso s3
    s3 = boto3.resource('s3', region_name = NAME_REGION)
    # Arquivo para upload
    data = open(local_file, 'rb')
    # Data e hora atual para adicionar ao nome do arquivo
    date = f"{datetime.today().strftime('%Y%m%d')}"
    # Faz o upload do arquivo pro s3, o 'Key' serve pro nome do arquivo no bucket
    # Body é o arquivo que será enviado
    s3.Bucket(NAME_BUCKET).put_object(Key=(f'RAW/ECOMMERCE/{date}/{nome_arquivo}'), Body=data)
    LOGGER.debug("Upload do arquivo " + nome_arquivo + " realizado no caminho RAW/ECOMMERCE/" + date)