import os
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

def bootstrap():
    region = os.getenv("AWS_REGION")
    bucket_silver_raw = os.getenv("BUCKET_SILVER")
    bucket_gold_raw = os.getenv("BUCKET_GOLD")
    db_silver = os.getenv("DATABASE_SILVER")
    db_gold = os.getenv("DATABASE_GOLD")

    # =================================================================
    # 🔍 PASSO 0: DIAGNÓSTICO DO ARQUIVO .ENV
    # =================================================================
    print("🔍 [PASSO 0] Verificando variáveis do arquivo .env...")
    config_ok = True
    variaveis = [
        ("AWS_REGION", region),
        ("BUCKET_SILVER", bucket_silver_raw),
        ("BUCKET_GOLD", bucket_gold_raw),
        ("DATABASE_SILVER", db_silver),
        ("DATABASE_GOLD", db_gold)
    ]
    
    for var_name, var_val in variaveis:
        if not var_val:
            print(f"  ❌ Erro: A variável '{var_name}' está ausente ou vazia no .env!")
            config_ok = False
        else:
            print(f"  • {var_name}: '{var_val}'")
    
    if not config_ok:
        print("\n🛑 Bootstrap abortado. Corrija o seu arquivo .env antes de prosseguir.")
        return

    # Inicializa os clientes da AWS
    s3 = boto3.client("s3", region_name=region)
    glue = boto3.client("glue", region_name=region)

    # Função auxiliar para limpar e isolar o nome do bucket
    def limpar_nome_bucket(url_ou_nome):
        return url_ou_nome.replace("s3://", "").strip().split("/")[0]

    buckets = {
        "Silver": limpar_nome_bucket(bucket_silver_raw),
        "Gold": limpar_nome_bucket(bucket_gold_raw)
    }

    databases = {
        "Silver": db_silver.strip(),  # type: ignore
        "Gold": db_gold.strip()  # type: ignore
    }  # type: ignore

    # =================================================================
    # 📦 PASSO 1: CRIAÇÃO DOS BUCKETS NO S3
    # =================================================================
    print("\n📦 [PASSO 1] Garantindo camadas de armazenamento no S3...")
    for camada, bucket_name in buckets.items():
        print(f"  🔄 Analisando bucket da camada {camada}: '{bucket_name}'...")
        try:
            s3.head_bucket(Bucket=bucket_name)
            print(f"    ✅ Sucesso: O bucket '{bucket_name}' já existe e você tem acesso.")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            # Código 404 significa que o bucket não existe de verdade. Vamos criá-lo!
            if error_code == '404':
                print(f"    ⚠️ O bucket não existe. Tentando criar na região '{region}'...")
                try:
                    if region == "us-east-1":
                        s3.create_bucket(Bucket=bucket_name)
                    else:
                        s3.create_bucket(
                            Bucket=bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': region}
                        )
                    print(f"    ✨ Sucesso: Bucket '{bucket_name}' criado do zero!")
                except ClientError as create_err:
                    print(f"    ❌ Erro crítico ao criar: {create_err.response['Error']['Message']}")
            
            # Código 403 significa que o nome já está tomado por OUTRA pessoa no planeta
            elif error_code == '403':
                print(f"    ❌ Erro de Conflito (403): O nome '{bucket_name}' já está ocupado globalmente por outro usuário AWS.")
                print("       💡 Ação: Altere o valor no seu .env para algo único (ex: seu-nome-foodwaste-silver).")
            else:
                print(f"    ❌ Erro inesperado no S3 ({error_code}): {e}")

    # =================================================================
    # 📚 PASSO 2: CRIAÇÃO DOS BANCOS DE DADOS NO GLUE
    # =================================================================
    print("\n📚 [PASSO 2] Garantindo catálogos de dados no AWS Glue...")
    for camada, db_name in databases.items():
        print(f"  🔄 Analisando banco de dados {camada}: '{db_name}'...")
        try:
            glue.get_database(Name=db_name)
            print(f"    ✅ Sucesso: O banco de dados '{db_name}' já mapeado no Glue.")
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityNotFoundException':
                print(f"    ⚠️ Banco '{db_name}' não encontrado. Inicializando criação...")
                try:
                    glue.create_database(
                        DatabaseInput={
                            'Name': db_name,
                            'Description': f'Data Catalog FoodWaste - Camada {camada}.'
                        }
                    )
                    print(f"    ✨ Sucesso: Banco de dados '{db_name}' criado no Glue Catalog!")
                except ClientError as create_db_err:
                    print(f"    ❌ Erro crítico ao criar banco no Glue: {create_db_err.response['Error']['Message']}")
            else:
                print(f"    ❌ Erro inesperado no Glue: {e}")

    print("\n🏆 [FIM] Processo de validação de infraestrutura concluído!")

if __name__ == "__main__":
    bootstrap()