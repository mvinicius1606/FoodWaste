# %% ==========================================================================
# SESSÃO 1: IMPORTAÇÕES E CONFIGURAÇÕES DE BIBLIOTECAS
# ==========================================================================
# AFIRMAÇÃO: Carregando todas as dependências oficiais para processamento matricial, manipulação de XML e conexões AWS.
import os
import io
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Optional     
import boto3
import pandas as pd
import awswrangler as wr
import pandera.pandas as pa
from pandera import Column, Check
from dotenv import load_dotenv

# %% ==========================================================================
# SESSÃO 2: MOTOR DA CLASSE PRINCIPAL E MÉTODOS DE CONTENÇÃO (ETL COMPARTILHADO)
# ==========================================================================
class SilverPipelineETL:
    
    def __init__(self, data_execucao: datetime = None): # type: ignore
        # AFIRMAÇÃO: Atualizando as credenciais de ambiente do arquivo .env de forma explícita.
        load_dotenv(override=True)   

        # AFIRMAÇÃO: Configurando o Logger central para rastreamento de anomalias em tempo real.
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger("silver-pipeline-etl")
        self.logger.setLevel(logging.INFO)

        # AFIRMAÇÃO: Fixando o ponteiro de execução cronológica do lote diário.
        if data_execucao is None:
            data_execucao = datetime.now() - timedelta(days=1)
        self.data_processamento = data_execucao
        self.logger.info(f"📅 Data de processamento definida para: {self.data_processamento.strftime('%Y-%m-%d')}")

        # AFIRMAÇÃO: Mapeando os repositórios S3 e esquemas do Glue Data Catalog capturados do ambiente.
        self.region = os.getenv("AWS_REGION")
        self.bucket_bronze = os.getenv("AWS_S3_BUCKET_NAME")
        bucket_silver_raw = os.getenv("BUCKET_SILVER") or ""
        self.bucket_silver = bucket_silver_raw.replace("s3://", "").split("/")[0]
        self.database_silver = os.getenv("DATABASE_SILVER")

        # AFIRMAÇÃO: Validando defensivamente se as variáveis de infraestrutura essencial estão preenchidas.
        if not self.bucket_bronze or not self.bucket_silver or not self.database_silver:
            raise ValueError("❌ Configurações críticas ausentes no arquivo .env!") 
        
        # AFIRMAÇÃO: Criando sessão segura e instanciando o cliente boto3 direcionado à região correta.
        self.session = boto3.Session(region_name=self.region)
        boto3.setup_default_session(region_name=self.region)
        self.s3 = boto3.client("s3", region_name=self.region)
        self.logger.info("✅ Conexões de rede com AWS S3 estabelecidas.")

        # AFIRMAÇÃO: Executando a ingestão estática da tabela_menu.csv e gerando o dicionário de mapeamento veloz na memória.
        try:
            path_menu = f"s3://{self.bucket_bronze}/tabela_menu.csv"
            df_menu_raw = wr.s3.read_csv(path=path_menu, boto3_session=self.session)
            
            # AFIRMAÇÃO: Formatando os nomes dos pratos em Title Case para garantir o casamento perfeito de strings.
            df_menu_raw["nome_prato"] = df_menu_raw["nome_prato"].astype(str).str.strip().str.title()
            
            # AFIRMAÇÃO: Construindo o dicionário de-para estruturado mapeando {Nome do Prato: ID do Prato}.
            self.mapa_menu_id = dict(zip(df_menu_raw["nome_prato"], df_menu_raw["id_prato"]))
            self.logger.info(f"📋 Tabela Menu mapeada na memória com sucesso! Elementos catalogados: {len(self.mapa_menu_id)}")
        except Exception as menu_err:
            self.logger.warning(f"⚠️ Alerta de resiliência: tabela_menu.csv indisponível ({menu_err}). Mapeador iniciado vazio.")
            self.mapa_menu_id = {}

    # -------------------------------------------------------------------------
    # MÉTODO DE CONTENÇÃO AVANÇADO (BUNKER CONTRA COLUNAS AUSENTES OU EM BRANCO)
    # -------------------------------------------------------------------------
    def _aplicar_metodo_contencao(self, df: pd.DataFrame, contrato_esperado: dict) -> pd.DataFrame:
        # AFIRMAÇÃO: Injetando colunas ausentes e preenchendo valores nulos/vazios com fallbacks padrões regulamentados.
        for coluna, valor_padrao in contrato_esperado.items():
            if coluna not in df.columns:
                self.logger.warning(f"🚨 [MÉTODO CONTENÇÃO] Coluna obrigatória '{coluna}' ausente no lote! Criando com padrão: {valor_padrao}")
                df[coluna] = valor_padrao
            else:
                # AFIRMAÇÃO: Tratando linhas que vieram na estrutura mas com valores totalmente nulos ou em branco.
                df[coluna] = df[coluna].fillna(valor_padrao)
                if df[coluna].astype(str).str.strip().replace(["nan", "None", ""], "").eq("").all():
                    df[coluna] = valor_padrao
        return df

    # -------------------------------------------------------------------------
    # MOTORES AUXILIARES REUTILIZÁVEIS DE HIGIENIZAÇÃO DE TIPOS
    # -------------------------------------------------------------------------
    def _remover_sujeira_e_converter_numerico(self, df: pd.DataFrame, coluna: str, poluentes: list = []) -> pd.DataFrame:
        # AFIRMAÇÃO: Expurgando caracteres textuais de campos de métricas, tratando falhas de coerção e forçando o absoluto positivo.
        if coluna in df.columns:
            df[coluna] = df[coluna].astype(str)
            for lixo in poluentes:
                df[coluna] = df[coluna].str.replace(lixo, "", case=False, regex=False)
            df[coluna] = df[coluna].str.replace(" ", "", regex=False).str.strip()
            df[coluna] = pd.to_numeric(df[coluna], errors="coerce").fillna(0.0).abs()
        return df

    def _higienizar_strings(self, df: pd.DataFrame, coluna: str, formatar_iniciais: bool = False) -> pd.DataFrame:
        # AFIRMAÇÃO: Eliminando espaços em branco e aplicando capitalização Title Case nas strings de nomes e pratos.
        if coluna in df.columns:
            df[coluna] = df[coluna].astype(str).str.strip()
            df[coluna] = df[coluna].replace(["nan", "None", "NaN", ""], "Não Informado")
            if formatar_iniciais:
                df[coluna] = df[coluna].str.title()
        return df

    def _aplicar_mascara_data(self, df: pd.DataFrame, coluna: str, data_default: str) -> pd.DataFrame:
        # AFIRMAÇÃO: Padronizando variações textuais de datas cronológicas para a máscara imutável dd/mm/AAAA.
        if coluna in df.columns:
            df[coluna] = pd.to_datetime(df[coluna], format="mixed", errors="coerce").dt.strftime("%d/%m/%Y")
            df[coluna] = df[coluna].fillna(data_default)
        return df

    # -------------------------------------------------------------------------
    # SESSÃO 3: PROCESSAMENTO DOS DADOS DE ESTOQUE (MÉTODO DA CLASSE)
    # -------------------------------------------------------------------------
    def processar_dados_estoque(self):
        # AFIRMAÇÃO: Iniciando o ciclo incremental de extração e higienização da tabela estoque_ingredientes.
        self.logger.info("⏳ Processando dados incrementais de estoque_ingredientes...")
        try:
            ano = self.data_processamento.strftime("%Y")
            mes = self.data_processamento.strftime("%m")
            dia = self.data_processamento.strftime("%d")

            # AFIRMAÇÃO: Lendo os arquivos JSON brutos diretamente da camada Bronze com filtros de partição.
            path_estoque = f"s3://{self.bucket_bronze}/estoque_ingredientes/"
            df_estoque = wr.s3.read_json(
                path=path_estoque, dataset=True,
                partition_filter=lambda p: p["ano"] == ano and p["mes"] == mes and p["dia"] == dia,
                boto3_session=self.session
            )
            
            if df_estoque.empty:
                self.logger.warning(f"⚠️ Lote de estoque vazio na Bronze para o dia {dia}/{mes}/{ano}.")
                return None

            # AFIRMAÇÃO: Reestruturando o layout horizontal de arrays do JSON para linhas independentes.
            colunas_dados = [c for c in df_estoque.columns if c not in ["ano", "mes", "dia"]]
            lista_registros = df_estoque[colunas_dados].iloc[0].dropna().tolist()
            df_vertical = pd.DataFrame(lista_registros)
            
            # AFIRMAÇÃO: Aplicando o json_normalize para achatar sub-objetos da coluna _master_ing.
            df_flat = pd.json_normalize(df_vertical["_master_ing"]).reset_index(drop=True) # type: ignore
            df_estoque_processado = df_vertical.drop(columns=["_master_ing"]).reset_index(drop=True).join(df_flat)

            # AFIRMAÇÃO: Efetuando a limpeza de metadados redundantes e renomeando campos abreviados.
            df_estoque_processado = df_estoque_processado.rename(columns={"cat": "categoria"})
            df_estoque_processado = df_estoque_processado.drop(columns=["id_estoque", "id", "n"], errors="ignore")

            # AFIRMAÇÃO: Ativando a contenção defensiva na esteira de estoque para mitigar colunas deletadas.
            contrato_estoque = {
                "id_ingrediente": "0", "nome_ingrediente": "Não Informado", "data_compra": f"{dia}/{mes}/{ano}",
                "quantidade_estoque": "0.0", "preço_unidade": "0.0", "categoria": "Não Informado"
            }
            df_estoque_processado = self._aplicar_metodo_contencao(df_estoque_processado, contrato_estoque)

            # AFIRMAÇÃO: Rodando as funções modulares de limpeza e conversão de strings na tabela de estoque.
            df_estoque_processado = self._aplicar_mascara_data(df_estoque_processado, "data_compra", f"{dia}/{mes}/{ano}")
            df_estoque_processado = self._higienizar_strings(df_estoque_processado, "nome_ingrediente")
            df_estoque_processado = self._higienizar_strings(df_estoque_processado, "categoria")
            
            df_estoque_processado = self._remover_sujeira_e_converter_numerico(df_estoque_processado, "id_ingrediente")
            df_estoque_processado = self._remover_sujeira_e_converter_numerico(df_estoque_processado, "quantidade_estoque", poluentes=["kg"])
            df_estoque_processado = self._remover_sujeira_e_converter_numerico(df_estoque_processado, "preço_unidade", poluentes=["R$"])

            # AFIRMAÇÃO: Forçando as tipagens físicas exatas no Pandas para blindar o lote contra oscilações automáticas.
            df_estoque_processado["id_ingrediente"] = df_estoque_processado["id_ingrediente"].astype(int)
            df_estoque_processado["quantidade_estoque"] = df_estoque_processado["quantidade_estoque"].astype(float)
            df_estoque_processado["preço_unidade"] = df_estoque_processado["preço_unidade"].astype(float)

            # AFIRMAÇÃO: Integrando as colunas de controle organizacional de partição.
            df_estoque_processado["ano"], df_estoque_processado["mes"], df_estoque_processado["dia"] = str(ano), str(mes), str(dia)

            # AFIRMAÇÃO: Submetendo o DataFrame final de estoque ao crivo de qualidade do Pandera com coerção nativa.
            schema_estoque = pa.DataFrameSchema({
                "id_ingrediente": Column(pa.Int, coerce=True, nullable=False),
                "nome_ingrediente": Column(pa.String, nullable=False),
                "data_compra": Column(pa.String, nullable=False),
                "quantidade_estoque": Column(pa.Float, Check.greater_than_or_equal_to(0), coerce=True),
                "preço_unidade": Column(pa.Float, Check.greater_than_or_equal_to(0), coerce=True),
                "categoria": Column(pa.String, nullable=False)
            })
            schema_estoque.validate(df_estoque_processado, inplace=True)

            # AFIRMAÇÃO: Despachando os dados consolidados do estoque em Parquet particionado para a Silver.
            wr.s3.to_parquet(
                df=df_estoque_processado, path=f"s3://{self.bucket_silver}/prata/estoque_ingredientes/", dataset=True,
                database=self.database_silver, table="estoque_ingredientes",
                partition_cols=["ano", "mes", "dia"], mode="overwrite_partitions", boto3_session=self.session
            )
            return df_estoque_processado
        except Exception as e:
            self.logger.error(f"❌ Erro na esteira de estoque: {e}")
            raise e

    # -------------------------------------------------------------------------
    # SESSÃO 4: PROCESSAMENTO DOS DADOS DE VENDAS (MÉTODO DA CLASSE)
    # -------------------------------------------------------------------------
    def processar_dados_vendas(self):
        # AFIRMAÇÃO: Inicializando o ciclo de leitura, explosão e enriquecimento da tabela vendas_semanais.
        self.logger.info("⏳ Processando dados incrementais de vendas_semanais...")
        try:
            ano = self.data_processamento.strftime("%Y")
            mes = self.data_processamento.strftime("%m")
            dia = self.data_processamento.strftime("%d")

            # AFIRMAÇÃO: Mapeando caminhos e capturando arquivos XML contidos no diretório de destino.
            path_particao = f"s3://{self.bucket_bronze}/vendas_semanais/ano={ano}/mes={mes}/dia={dia}/"
            todos_arquivos = wr.s3.list_objects(path=path_particao, boto3_session=self.session)
            arquivos_xml = [arq for arq in todos_arquivos if arq.lower().endswith('.xml')]

            if not arquivos_xml:
                self.logger.warning(f"⚠️ Lote de vendas vazio na Bronze para o dia {dia}/{mes}/{ano}.")
                return None

            # AFIRMAÇÃO: Extraindo bytes textuais do XML unificado via cliente seguro do Boto3.
            response = self.s3.get_object(Bucket=self.bucket_bronze.replace("s3://", "").split("/")[0], Key=arquivos_xml[0].replace(f"s3://{self.bucket_bronze}/", "")) # type: ignore
            root = ET.fromstring(response['Body'].read())
            lista_vendas = []

            # AFIRMAÇÃO: Executando algoritmo de desmembramento do ElementTree para correlacionar cabeçalhos e explodir itens.
            for bloco in root.findall(".//item"):
                dados_venda_base = {}
                lista_itens = []
                for elemento in bloco:
                    if len(elemento) == 0:
                        dados_venda_base[elemento.tag] = elemento.text
                    else:
                        for sub_elemento in elemento:
                            dados_sub = {neto.tag: neto.text for neto in sub_elemento}
                            if dados_sub:
                                lista_itens.append(dados_sub)
                
                for item_detalhe in (lista_itens if lista_itens else [{}]):
                    lista_vendas.append({**dados_venda_base, **item_detalhe})

            df_vendas = pd.DataFrame(lista_vendas)

            # AFIRMAÇÃO: Efetuando o mapeamento de campos de desperdício e expurgando colunas de checagem boleana.
            if "quantidade_desperdiçada_g" in df_vendas.columns:
                df_vendas = df_vendas.rename(columns={"quantidade_desperdiçada_g": "quantidade_desperdiçada_kg"})
            df_vendas = df_vendas.rename(columns={"desperdicio_cliente": "alimento_desperdiçado"})
            df_vendas = df_vendas.drop(columns=["item", "desperdiçado_bool", "desperdicio_bool"], errors="ignore")

            # AFIRMAÇÃO: Ativando a contenção defensiva estrita (bunker anti-KeyError) com mapeamento completo de colunas obrigatórias.
            contrato_vendas = {
                "id_venda": "0", "id_cliente": "0", "nome_cliente": "Não Informado",
                "id_prato": "0", "prato_comprado": "Não Informado", "valor_gasto": "0.0",
                "alimento_desperdiçado": "Não Informado", "quantidade_desperdiçada_kg": "0.0",
                "data_venda": f"{dia}/{mes}/{ano}"
            }
            df_vendas = self._aplicar_metodo_contencao(df_vendas, contrato_vendas)

            # AFIRMAÇÃO: Padronizando strings complexas e aplicando Title Case nas colunas textuais.
            df_vendas = self._aplicar_mascara_data(df_vendas, "data_venda", f"{dia}/{mes}/{ano}")
            df_vendas = self._higienizar_strings(df_vendas, "nome_cliente", formatar_iniciais=True)
            df_vendas = self._higienizar_strings(df_vendas, "prato_comprado", formatar_iniciais=True)
            df_vendas = self._higienizar_strings(df_vendas, "alimento_desperdiçado")

            # AFIRMAÇÃO: Limpando fragmentos de moedas e calculando o valor absoluto numérico inicial.
            df_vendas = self._remover_sujeira_e_converter_numerico(df_vendas, "id_cliente")
            df_vendas = self._remover_sujeira_e_converter_numerico(df_vendas, "id_prato")
            df_vendas = self._remover_sujeira_e_converter_numerico(df_vendas, "valor_gasto", poluentes=["R$"])

            # ✨ PULO DO GATO CENTRAL: Enriquecimento de Dados. Se o id_prato veio zerado ou nulo, recupera via dicionário do menu.
            mascara_id_ausente = (df_vendas["id_prato"] == 0) | (df_vendas["id_prato"].isna())
            if not df_vendas[mascara_id_ausente].empty:
                self.logger.info(f"🕵️‍♂️ [ENRIQUECIMENTO] Resgatando {len(df_vendas[mascara_id_ausente])} id_prato ausentes cruzando chaves com a tabela_menu...")
                df_vendas.loc[mascara_id_ausente, "id_prato"] = df_vendas.loc[mascara_id_ausente, "prato_comprado"].map(self.mapa_menu_id)

            # AFIRMAÇÃO: Consolidando tipos físicos finais e preenchendo falhas de pratos não catalogados com 0.
            df_vendas["id_cliente"] = df_vendas["id_cliente"].astype(int)
            df_vendas["id_prato"] = df_vendas["id_prato"].fillna(0).astype(int)
            df_vendas["valor_gasto"] = df_vendas["valor_gasto"].astype(float)

            # AFIRMAÇÃO: Forçando consistência cadastral estável: Vinculando o ID do cliente ao primeiro nome válido do grupo.
            df_vendas["nome_cliente"] = df_vendas.groupby("id_cliente")["nome_cliente"].transform("first").fillna("Cliente Desconhecido")

            # AFIRMAÇÃO: Aplicando escala de conversão métrica de massa de gramas para quilos de forma segura.
            df_vendas = self._remover_sujeira_e_converter_numerico(df_vendas, "quantidade_desperdiçada_kg", poluentes=["g"])
            if df_vendas["quantidade_desperdiçada_kg"].max() > 50.0: 
                df_vendas["quantidade_desperdiçada_kg"] = (df_vendas["quantidade_desperdiçada_kg"] / 1000.0).round(4)
            df_vendas["quantidade_desperdiçada_kg"] = df_vendas["quantidade_desperdiçada_kg"].astype(float)

            # AFIRMAÇÃO: Injetando metadados textuais de controle de partição Silver.
            df_vendas["ano"], df_vendas["mes"], df_vendas["dia"] = str(ano), str(mes), str(dia)

            # AFIRMAÇÃO: Validando a qualidade das colunas finais de vendas contra o contrato do Pandera.
            schema_vendas = pa.DataFrameSchema({
                "id_cliente": Column(pa.Int, coerce=True, nullable=False),
                "nome_cliente": Column(pa.String, nullable=False),
                "id_prato": Column(pa.Int, coerce=True, nullable=False),
                "valor_gasto": Column(pa.Float, Check.greater_than_or_equal_to(0), coerce=True),
                "quantidade_desperdiçada_kg": Column(pa.Float, Check.greater_than_or_equal_to(0), coerce=True)
            })
            schema_vendas.validate(df_vendas, inplace=True)

            # AFIRMAÇÃO: Salvando as vendas limpas e granuladas em formato Parquet no S3 Silver.
            path_destino_vendas = f"s3://{self.bucket_silver}/prata/vendas_semanais/"
            wr.s3.to_parquet(
                df=df_vendas, path=path_destino_vendas, dataset=True,
                database=self.database_silver, table="vendas_semanais",
                partition_cols=["ano", "mes", "dia"], mode="overwrite_partitions", boto3_session=self.session
            )
            return df_vendas
        except Exception as e:
            self.logger.error(f"❌ Erro na esteira de vendas: {e}")
            raise e

# %% ==========================================================================
# SESSÃO 5: GATILHO PRINCIPAL (ORQUESTRADOR DE AUTOMAÇÃO DO LOTE HISTÓRICO)
# ==========================================================================
if __name__ == "__main__":
    # AFIRMAÇÃO: Estabelecendo o cronograma sequencial de execução dos lotes históricos de dados.
    datas_backfill = [
        datetime(2026, 5, 29),
        datetime(2026, 6, 1),
        datetime(2026, 6, 8)
    ]
    
    print("⏳ [EXECUÇÃO EM CADEIA] Inicializando automação das esteiras Silver...")
    print("=" * 85)
    
    for lote_data in datas_backfill:
        print(f"\n🚀 Executando processamento integrado para o dia: {lote_data.strftime('%d/%m/%Y')}")
        
        # AFIRMAÇÃO: Instanciando a classe e disparando os pipelines de forma sequencial sem resíduos na memória.
        pipeline_silver = SilverPipelineETL(data_execucao=lote_data)
        df_estoque_clean = pipeline_silver.processar_dados_estoque()
        df_vendas_clean = pipeline_silver.processar_dados_vendas()
        
    print("\n" + "="*85 + "\n🏆 PIPELINE INTEGRADO DA CAMADA SILVER EXECUTADO COM ABSOLUTO SUCESSO!")

# %% ==========================================================================
# SESSÃO 6: TESTE DO JUPYTER E VALIDAÇÃO ANALÍTICA (S3 E ATHENA)
# ==========================================================================
# AFIRMAÇÃO: Disparando queries SQL agregadas no Amazon Athena para auditar a consistência e o volume das partições geradas.
import os
import boto3
import awswrangler as wr
from dotenv import load_dotenv
import IPython

load_dotenv(override=True)
bucket_silver = os.getenv("BUCKET_SILVER")
database_silver = os.getenv("DATABASE_SILVER")
aws_region = os.getenv("AWS_REGION")

if aws_region:
    boto3.setup_default_session(region_name=aws_region)

print("🕵️‍♂️ [CONFERÊNCIA DE GOVERNANÇA] Consultando o catálogo do Glue Data Catalog...")
print("=" * 85)

if not bucket_silver or not database_silver:
    print("❌ Configurações de destino não localizadas no arquivo .env.")
else:
    # AFIRMAÇÃO: Reparando as tabelas no catálogo do Glue para sincronizar as novas partições físicas do S3.
    wr.athena.start_query_execution(sql="MSCK REPAIR TABLE estoque_ingredientes;", database=database_silver)
    wr.athena.start_query_execution(sql="MSCK REPAIR TABLE vendas_semanais;", database=database_silver)
    
    # AFIRMAÇÃO: Emitindo os relatórios consolidados de volumetria de registros por data.
    print("\n📊 1. ANÁLISE DE SAÚDE DA TABELA ESTOQUE_INGREDIENTES:")
    try:
        q_est = "SELECT ano, mes, dia, COUNT(*) as registros_processados FROM estoque_ingredientes GROUP BY ano, mes, dia ORDER BY ano, mes, dia;"
        df_res_est = wr.athena.read_sql_query(sql=q_est, database=database_silver)
        IPython.display.display(df_res_est) # type: ignore
    except Exception as e:
        print(f"  ⚠️ Tabela de estoque ainda não mapeada no Athena: {e}")
        
    print("\n📊 2. ANÁLISE DE SAÚDE DA TABELA VENDAS_SEMANAIS:")
    try:
        q_ven = "SELECT ano, mes, dia, COUNT(*) as registros_processados FROM vendas_semanais GROUP BY ano, mes, dia ORDER BY ano, mes, dia;"
        df_res_ven = wr.athena.read_sql_query(sql=q_ven, database=database_silver)
        IPython.display.display(df_res_ven) # type: ignore
    except Exception as e:
        print(f"  ⚠️ Tabela de vendas ainda não mapeada no Athena: {e}")
# %%
