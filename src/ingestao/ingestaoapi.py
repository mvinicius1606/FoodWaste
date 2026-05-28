import os
import logging
from random import random
import httpx 
import asyncio
import boto3 
import watchtower 
from datetime import datetime   
from dotenv import load_dotenv
from botocore.exceptions import ClientError
import json 
import dicttoxml
import random
from fastapi import BackgroundTasks, FastAPI, HTTPException

load_dotenv()

logger = logging.getLogger("ingestao-foodwaste-pipeline")
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

try:
    cliente_aws = boto3.client(
        'logs',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION')
    )

    # Ajustado o nome da variável aqui para 'cloudwatch_handler'
    cloudwatch_handler = watchtower.CloudWatchLogHandler(
        boto3_client=cliente_aws, 
        log_group_name="FoodWasteLogs"
    )

    # Agora o nome bate perfeitamente!
    logger.addHandler(cloudwatch_handler)
    logger.info("CloudWatch logging configured successfully.")  

except Exception as e:
    logger.error(f"Failed to configure CloudWatch logging: {e}")

app = FastAPI(title="Ingestão API", description="API para ingestão de dados de desperdício de alimentos", version="1.0")   

def executar_pipeline_vendas():
    api_vendas_url = os.getenv('VENDAS_SEMANAIS_URL')
    bucket_name = os.getenv('AWS_S3_BUCKET_NAME')
    
    if not api_vendas_url or not bucket_name:
        logger.error("Configurações ausentes! Verifique as variáveis VENDAS_SEMANAIS_URL e AWS_S3_BUCKET_NAME no seu .env.")
        return
        
    try:
        logger.info("Iniciando pipeline de ingestão de vendas semanais.")

        numero_linhas = random.randint(500,1000)
        api_vendas_url_linhas = f"{api_vendas_url}&count={numero_linhas}"

        response = httpx.get(api_vendas_url_linhas, timeout=30)

        if response.status_code != 200:
            logger.error(f"Erro na requisição para a pipeline de vendas: {response.status_code} - {response.text}")
            return
                
        dados_vendas = response.json()
    except httpx.RequestError as e:
        logger.error(f"Erro na requisição para a pipeline de vendas: {e}")
        return

    agora = datetime.utcnow()
    s3_key = f"vendas_semanais/ano={agora.strftime('%Y')}/mes={agora.strftime('%m')}/dia={agora.strftime('%d')}/vendas_{agora.strftime('%H-%M-%S')}.xml"

    try:
        logger.info(f"Conectando ao S3 via cliente boto3 para salvar os dados de vendas semanais.")
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION'))   
        
        logger.info(f"Conexão com S3 estabelecida. Salvando dados no bucket '{bucket_name}' com a chave.")
        s3_client.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=dicttoxml.dicttoxml({'vendas': dados_vendas}, attr_type=False),
                ContentType='application/xml')
        logger.info(f"Dados de vendas semanais salvos com sucesso no S3 em '{bucket_name}.")

    except Exception as e:
        logger.error(f"Erro ao salvar os dados de vendas semanais no S3: {e}")
        return

@app.post("/ingestao/vendas-semanais", summary="Ingestão de vendas semanais", description="Executa a pipeline de ingestão de vendas semanais e salva os dados no S3.", status_code=202)
def disparar_ingestao_vendas(background_tasks: BackgroundTasks):
    logger.info("Endpoint HTTP GET '/vendas/ingestao' foi acionado.")
    background_tasks.add_task(executar_pipeline_vendas)
    return {"status": "Processamento de vendas iniciado em segundo plano"}

def executar_pipeline_ingredientes():
    api_url = os.getenv('ESTOQUE_INGREDIENTES_URL')
    bucket_name = os.getenv('AWS_S3_BUCKET_NAME')
    
    if not api_url or not bucket_name:
        logger.error("Configurações ausentes! Verifique as variáveis ESTOQUE_INGREDIENTES_URL e AWS_S3_BUCKET_NAME no seu .env.")
        return    
    try:
        logger.info("Iniciando pipeline de ingestão de estoque de ingredientes.")
        response = httpx.get(api_url, timeout=30)

        if response.status_code != 200:
            logger.error(f"Erro na requisição para a pipeline de ingredientes: {response.status_code} - {response.text}")
            return
        
        dados_ingredientes = response.json()
        logger.info(f"Pipeline de ingredientes concluída com sucesso. Dados recebidos: {len(dados_ingredientes)} registros")

    except httpx.RequestError as e:
        logger.error(f"Erro na requisição para a pipeline de ingredientes: {e}")
        return
    
    agora = datetime.utcnow()
    s3_key = f"estoque_ingredientes/ano={agora.strftime('%Y')}/mes={agora.strftime('%m')}/dia={agora.strftime('%d')}/ingredientes_{agora.strftime('%H-%M-%S')}.json"

    try:
        logger.info(f"Conectando ao S3 via cliente boto3 para salvar os dados de estoque de ingredientes.")
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION'))   
        
        logger.info(f"Conexão com S3 estabelecida. Salvando dados no bucket '{bucket_name}' com a chave.")
        s3_client.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=json.dumps(dados_ingredientes, ensure_ascii=False),
                ContentType='application/json')
        logger.info(f"Dados de estoque de ingredientes salvos com sucesso no S3 em '{bucket_name}.")

    except Exception as e:
        logger.error(f"Erro ao salvar os dados de estoque de ingredientes no S3: {e}")
        return

@app.post("/ingestao/estoque-ingredientes", summary="Ingestão de estoque de ingredientes", description="Executa a pipeline de ingestão de estoque de ingredientes e salva os dados no S3.", status_code=202)
def disparar_ingestao_ingredientes(background_tasks: BackgroundTasks):  
    logger.info("Endpoint HTTP GET '/ingredientes/ingestao' foi acionado.")
    background_tasks.add_task(executar_pipeline_ingredientes)
    return {"status": "Processamento de estoque de ingredientes iniciado em segundo plano"}   