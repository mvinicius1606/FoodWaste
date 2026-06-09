# %% ==========================================================================
# SESSÃO 1: IMPORTAÇÕES E CONFIGURAÇÕES DE BIBLIOTECAS
# ==========================================================================
# AFIRMAÇÃO: Carregando todas as dependências oficiais para processamento matricial, validação e conexões AWS.
import os
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import boto3
import pandas as pd
import awswrangler as wr
import pandera.pandas as pa
from pandera import Column, Check
from dotenv import load_dotenv
import IPython

# %% ==========================================================================
# SESSÃO 2: CLASSE PRINCIPAL E CONSTRUTOR DE INFRAESTRUTURA
# ==========================================================================
class SilverPipelineETL:
    
    def __init__(self, data_execucao: datetime = None):
        # AFIRMAÇÃO: Atualizando as credenciais de ambiente do arquivo .env de forma explícita.
        load_dotenv(override=True)   

        # AFIRMAÇÃO: Configurando o Logger central para rastreamento de anomalias em tempo real.
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger("silver-pipeline-etl")

        # AFIRMAÇÃO: Fixando o ponteiro de execução cronológica do lote diário (Default: Ontem para Automação).
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

        if not self.bucket_bronze or not self.bucket_silver or not self.database_silver:
            raise ValueError("❌ Configurações críticas ausentes no arquivo .env!") 
        
        # AFIRMAÇÃO: Criando sessão segura e instanciando o cliente boto3.
        self.session = boto3.Session(region_name=self.region)
        boto3.setup_default_session(region_name=self.region)
        self.s3 = boto3.client("s3", region_name=self.region)

# ==========================================================================
# SESSÃO 3: PROCESSAMENTO DOS DADOS DE ESTOQUE (ESTEIRA COMPROVADA)
# ==========================================================================
    def processar_dados_estoque(self):
        self.logger.info("⏳ Processando dados incrementais de estoque_ingredientes...")
        try:
            ano, mes, dia = self.data_processamento.strftime("%Y"), self.data_processamento.strftime("%m"), self.data_processamento.strftime("%d")

            path_estoque = f"s3://{self.bucket_bronze}/estoque_ingredientes/"
            df_estoque = wr.s3.read_json(
                path=path_estoque, dataset=True,
                partition_filter=lambda p: p["ano"] == ano and p["mes"] == mes and p["dia"] == dia,
                boto3_session=self.session
            )
            
            if df_estoque.empty:
                self.logger.warning("⚠️ Lote de estoque vazio na Bronze.")
                return None

            # AFIRMAÇÃO: Achatando a estrutura horizontal de arrays do JSON.
            colunas_dados = [c for c in df_estoque.columns if c not in ["ano", "mes", "dia"]]
            lista_registros = df_estoque[colunas_dados].iloc[0].dropna().tolist()
            df_vertical = pd.DataFrame(lista_registros)
            
            df_flat = pd.json_normalize(df_vertical["_master_ing"]).reset_index(drop=True)
            df_estoque_clean = df_vertical.drop(columns=["_master_ing"]).reset_index(drop=True).join(df_flat)

            # AFIRMAÇÃO: Renomeando abreviações e expurgando metadados redundantes.
            df_estoque_clean = df_estoque_clean.rename(columns={"cat": "categoria"})
            df_estoque_clean = df_estoque_clean.drop(columns=["id_estoque", "id", "n"], errors="ignore")

            # AFIRMAÇÃO: Limpeza, máscaras cronológicas e tratamento de caracteres textuais de moedas e pesos.
            df_estoque_clean["data_compra"] = pd.to_datetime(df_estoque_clean["data_compra"], format="mixed", errors="coerce").dt.strftime("%d/%m/%Y")
            df_estoque_clean["data_compra"] = df_estoque_clean["data_compra"].fillna(f"{dia}/{mes}/{ano}")
            
            df_estoque_clean["nome_ingrediente"] = df_estoque_clean["nome_ingrediente"].astype(str).str.strip().str.title().replace(["Nan", "None", ""], "Não Informado")
            df_estoque_clean["categoria"] = df_estoque_clean["categoria"].astype(str).str.strip().str.title().replace(["Nan", "None", ""], "Não Informado")
            
            df_estoque_clean["id_ingrediente"] = pd.to_numeric(df_estoque_clean["id_ingrediente"], errors="coerce").fillna(0).astype(int).abs()
            
            df_estoque_clean["quantidade_estoque"] = df_estoque_clean["quantidade_estoque"].astype(str).str.replace("kg", "", case=False, regex=False).str.replace(" ", "")
            df_estoque_clean["quantidade_estoque"] = pd.to_numeric(df_estoque_clean["quantidade_estoque"], errors="coerce").fillna(0.0).astype(float).abs()

            df_estoque_clean["preço_unidade"] = df_estoque_clean["preço_unidade"].astype(str).str.replace("R$", "", case=False, regex=False).str.replace(" ", "")
            df_estoque_clean["preço_unidade"] = pd.to_numeric(df_estoque_clean["preço_unidade"], errors="coerce").fillna(0.0).astype(float).abs()

            df_estoque_clean["ano"], df_estoque_clean["mes"], df_estoque_clean["dia"] = str(ano), str(mes), str(dia)

            # AFIRMAÇÃO: Validação de Qualidade de Dados com o Pandera.
            schema_estoque = pa.DataFrameSchema({
                "id_ingrediente": Column(pa.Int, coerce=True, nullable=False),
                "nome_ingrediente": Column(pa.String, nullable=False),
                "data_compra": Column(pa.String, nullable=False),
                "quantidade_estoque": Column(pa.Float, Check.greater_than_or_equal_to(0.0), coerce=True),
                "preço_unidade": Column(pa.Float, Check.greater_than_or_equal_to(0.0), coerce=True),
                "categoria": Column(pa.String, nullable=False)
            })
            schema_estoque.validate(df_estoque_clean, inplace=True)

            # AFIRMAÇÃO: Persistindo os dados do estoque na camada Silver.
            wr.s3.to_parquet(
                df=df_estoque_clean, path=f"s3://{self.bucket_silver}/prata/estoque_ingredientes/", dataset=True,
                database=self.database_silver, table="estoque_ingredientes",
                partition_cols=["ano", "mes", "dia"], mode="overwrite_partitions", boto3_session=self.session
            )
            return df_estoque_clean
        except Exception as e:
            self.logger.error(f"❌ Erro na esteira de estoque: {e}")
            raise e

# ==========================================================================
# SESSÃO 4: PROCESSAMENTO DOS DADOS DE VENDAS (ESTEIRA COM ÂNCORA DA VERDADE)
# ==========================================================================
    def processar_dados_vendas(self):
        self.logger.info("⏳ Processando dados incrementais de vendas_semanais...")
        try:
            ano, mes, dia = self.data_processamento.strftime("%Y"), self.data_processamento.strftime("%m"), self.data_processamento.strftime("%d")

            # -------------------------------------------------------------------------
            # FASE 1: EXTRAÇÃO DO MENU E ENVIO DO 'DICIONARIO_PRATOS' PARA A SILVER
            # -------------------------------------------------------------------------
            path_menu = f"s3://{self.bucket_bronze}/tabela_menu.csv"
            df_menu = wr.s3.read_csv(path=path_menu, boto3_session=self.session)
            
            df_menu["id_prato"] = df_menu["id_prato"].astype(int)
            df_menu["prato"] = df_menu["prato"].astype(str).str.strip().str.title()
            df_menu["ingrediente"] = df_menu["ingrediente"].astype(str).str.strip().str.title()
            df_menu["qtd_base_kg"] = df_menu["qtd_base_kg"].astype(float)
            df_menu["preço_venda"] = df_menu["preço_venda"].astype(str).str.replace("R$", "", case=False, regex=False).str.replace(" ", "")
            df_menu["preço_venda"] = pd.to_numeric(df_menu["preço_venda"], errors="coerce").fillna(0.0).astype(float)

            # REQUISITO: Salvando o Dicionário de Pratos na camada Silver
            df_dic_pratos = df_menu[["id_prato", "prato", "preço_venda"]].drop_duplicates().reset_index(drop=True)
            wr.s3.to_parquet(
                df=df_dic_pratos, path=f"s3://{self.bucket_silver}/prata/dicionario_pratos/", dataset=True,
                database=self.database_silver, table="dicionario_pratos", mode="overwrite", boto3_session=self.session
            )

            # AFIRMAÇÃO: Indexando as Tabelas Hash em memória (Tempo O(1) de busca).
            dict_menu_preco = dict(zip(df_menu["id_prato"], df_menu["preço_venda"]))
            dict_menu_id_to_nome = dict(zip(df_menu["id_prato"], df_menu["prato"]))
            dict_menu_nome_to_id = dict(zip(df_menu["prato"], df_menu["id_prato"]))
            dict_menu_ingredientes = df_menu.groupby("id_prato")["ingrediente"].apply(list).to_dict()
            dict_menu_qtd_base = df_menu.set_index(["id_prato", "ingrediente"])["qtd_base_kg"].to_dict()

            # -------------------------------------------------------------------------
            # FASE 2: EXTRAÇÃO AND PARSER DIRECIONADO DO XML DE VENDAS
            # -------------------------------------------------------------------------
            path_particao = f"s3://{self.bucket_bronze}/vendas_semanais/ano={ano}/mes={mes}/dia={dia}/"
            todos_arquivos = wr.s3.list_objects(path=path_particao, boto3_session=self.session)
            arquivos_xml = [arq for arq in todos_arquivos if arq.lower().endswith('.xml')]

            if not arquivos_xml:
                self.logger.warning("⚠️ Lote de vendas vazio na Bronze.")
                return None

            response = self.s3.get_object(Bucket=self.bucket_bronze.replace("s3://", "").split("/")[0], Key=arquivos_xml[0].replace(f"s3://{self.bucket_bronze}/", ""))
            root = ET.fromstring(response['Body'].read())
            lista_vendas = []

            # ✨ ENGENHARIA ANTI-ANINHAMENTO: Captura apenas os elementos planos da transação primária
            for item_venda in root.findall("./vendas/item"):
                dados_linha = {}
                for elem in item_venda:
                    tag_limpa = elem.tag.lower().strip()
                    if tag_limpa != "_master_venda" and elem.text:
                        dados_linha[tag_limpa] = elem.text.strip()
                if dados_linha:
                    lista_vendas.append(dados_linha)

            df_vendas = pd.DataFrame(lista_vendas)

            # -------------------------------------------------------------------------
            # FASE 3: MAPEAmento DEFENSIVO E REMOÇÃO CIRÚRGICA DE COLUNAS SOLICITADAS
            # -------------------------------------------------------------------------
            # AFIRMAÇÃO: Copia os valores das colunas originais antes da exclusão estrutural para garantir a carga.
            if "id_prato_fk" in df_vendas.columns:
                df_vendas["id_prato"] = df_vendas["id_prato_fk"]
            if "desperdicio_clientes" in df_vendas.columns:
                df_vendas["alimento_desperdiçado"] = df_vendas["desperdicio_clientes"]
            if "quantidade_desperdiçada_g" in df_vendas.columns:
                df_vendas["quantidade_desperdiçada_kg"] = df_vendas["quantidade_desperdiçada_g"]

            # ✨ REQUISITO IMPERATIVO: Remoção explícita de todas as colunas de lixo estrutural e antigas chaves
            df_vendas = df_vendas.drop(columns=["id_prato_fk", "desperdicio_clientes", "id", "n", "p", "quantidade_desperdiçada_g"], errors="ignore")

            # AFIRMAÇÃO: Garante que as colunas de destino existam na contenção pós-drop
            for col_target in ["id_prato", "alimento_desperdiçado", "quantidade_desperdiçada_kg"]:
                if col_target not in df_vendas.columns:
                    df_vendas[col_target] = None

            # -------------------------------------------------------------------------
            # FASE 4: HIGIENIZAÇÃO CRONOLÓGICA E CONVERSÃO DE TIPOS PRIMITIVOS
            # -------------------------------------------------------------------------
            df_vendas["data_venda"] = pd.to_datetime(df_vendas["data_venda"], format="mixed", errors="coerce").dt.strftime("%d/%m/%Y")
            df_vendas["data_venda"] = df_vendas["data_venda"].fillna(f"{dia}/{mes}/{ano}")

            df_vendas["id_venda"] = pd.to_numeric(df_vendas["id_venda"], errors="coerce").fillna(0).astype(int).abs()
            df_vendas["id_cliente"] = pd.to_numeric(df_vendas["id_cliente"], errors="coerce").fillna(0).astype(int).abs()
            df_vendas["id_prato"] = pd.to_numeric(df_vendas["id_prato"], errors="coerce").fillna(0).astype(int).abs()

            df_vendas["desperdicio_bool"] = df_vendas["desperdicio_bool"].astype(str).str.strip().str.lower()
            df_vendas["desperdicio_bool"] = df_vendas["desperdicio_bool"].map({"true": True, "false": False, "1": True, "0": False}).fillna(False).astype(bool)

            # -------------------------------------------------------------------------
            # FASE 5: BUNKER DE CLIENTES E ENVIO DO 'DICIONARIO_CLIENTES' PARA A SILVER
            # -------------------------------------------------------------------------
            df_vendas["nome_cliente"] = df_vendas["nome_cliente"].astype(str).str.strip().str.title().replace(["None", "Nan", "NaN", ""], pd.NA)
            
            df_valid_cts = df_vendas[(df_vendas["id_cliente"] > 0) & (df_vendas["nome_cliente"].notna())]
            dict_clientes_id_to_nome = dict(zip(df_valid_cts["id_cliente"], df_valid_cts["nome_cliente"]))
            dict_clientes_nome_to_id = dict(zip(df_valid_cts["nome_cliente"], df_valid_cts["id_cliente"]))

            # REQUISITO: Salvando o Dicionário de Clientes consolidando o histórico na Silver
            df_dic_clientes = pd.DataFrame(list(dict_clientes_id_to_nome.items()), columns=["id_cliente", "nome_cliente"])
            wr.s3.to_parquet(
                df=df_dic_clientes, path=f"s3://{self.bucket_silver}/prata/dicionario_clientes/", dataset=True,
                database=self.database_silver, table="dicionario_clientes", mode="overwrite", boto3_session=self.session
            )

            # AFIRMAÇÃO: Corrigindo e autopreenchendo lacunas cadastrais via tabelas hash de clientes.
            mascara_nome_missing = df_vendas["nome_cliente"].isna()
            if mascara_nome_missing.any():
                df_vendas.loc[mascara_nome_missing, "nome_cliente"] = df_vendas.loc[mascara_nome_missing, "id_cliente"].map(dict_clientes_id_to_nome)

            mascara_id_missing = df_vendas["id_cliente"] == 0
            if mascara_id_missing.any():
                df_vendas.loc[mascara_id_missing, "id_cliente"] = df_vendas.loc[mascara_id_missing, "nome_cliente"].map(dict_clientes_nome_to_id).fillna(0).astype(int)

            df_vendas["nome_cliente"] = df_vendas["nome_cliente"].fillna("Cliente Desconhecido")

            # -------------------------------------------------------------------------
            # FASE 6: SINCRONIZAÇÃO DE CARDÁPIO E BLINDAGEM DE PREÇO (VALOR GASTO)
            # -------------------------------------------------------------------------
            df_vendas["prato_comprado"] = df_vendas["prato_comprado"].astype(str).str.strip().str.title().replace(["None", "Nan", ""], pd.NA)
            
            mascara_prato_id_zero = df_vendas["id_prato"] == 0
            if mascara_prato_id_zero.any():
                df_vendas.loc[mascara_prato_id_zero, "id_prato"] = df_vendas.loc[mascara_prato_id_zero, "prato_comprado"].map(dict_menu_nome_to_id).fillna(0).astype(int)

            # AFIRMAÇÃO: Forçando o alinhamento nominal com o menu oficial e injetando o Preço de Venda tabelado.
            df_vendas["prato_comprado"] = df_vendas["id_prato"].map(dict_menu_id_to_nome).fillna(df_vendas["prato_comprado"]).fillna("Não Informado")
            df_vendas["valor_gasto"] = df_vendas["id_prato"].map(dict_menu_preco).fillna(0.0).astype(float)

            # -------------------------------------------------------------------------
            # FASE 7: MOTOR DE AUDITORIA DE COMPOSIÇÃO DE RECEITAS E CLAMPING DE MASSA
            # -------------------------------------------------------------------------
            df_vendas["quantidade_desperdiçada_kg"] = df_vendas["quantidade_desperdiçada_kg"].astype(str).str.replace("g", "", case=False, regex=False).str.replace(" ", "")
            df_vendas["quantidade_desperdiçada_kg"] = pd.to_numeric(df_vendas["quantidade_desperdiçada_kg"], errors="coerce").fillna(0.0).astype(float)

            def aplicar_auditoria_receita(row, menu_ingredientes, menu_qtd_base):
                id_p, is_desp, qtd_desp = row["id_prato"], row["desperdicio_bool"], row["quantidade_desperdiçada_kg"]
                ing_desp = str(row["alimento_desperdiçado"]).strip().title()
                
                ingredientes_permitidos = menu_ingredientes.get(id_p, [])
                if not is_desp or not ingredientes_permitidos:
                    return "Não Informado", 0.0
                    
                # ✨ REGRA DE INTEGRALIDADE: Substitui insumos alucinados pelo primeiro ingrediente real da receita
                ing_final = ing_desp if ing_desp in ingredientes_permitidos else ingredientes_permitidos[0]
                peso_maximo_permitido = menu_qtd_base.get((id_p, ing_final), 0.0)
                
                if qtd_desp > 50.0:
                    qtd_desp = qtd_desp / 1000.0
                    
                # ✨ TRAVA FÍSICA (CLAMPING): Impede que o desperdício seja maior que o peso base da receita
                if qtd_desp > peso_maximo_permitido:
                    qtd_desp = peso_maximo_permitido
                    
                return ing_final, round(qtd_desp, 4)

            # AFIRMAÇÃO: Executando o motor de auditoria tridimensional protegendo o escopo por argumentos de tupla.
            df_vendas[["alimento_desperdiçado", "quantidade_desperdiçada_kg"]] = df_vendas.apply(
                aplicar_auditoria_receita, axis=1, result_type="expand", args=(dict_menu_ingredientes, dict_menu_qtd_base)
            )

            # AFIRMAÇÃO: Consolidação final do Layout estrito do Contrato Silver (Garante descarte absoluto de sobras).
            colunas_contrato_silver = [
                "id_venda", "id_cliente", "nome_cliente", "id_prato", "prato_comprado",
                "data_venda", "valor_gasto", "alimento_desperdiçado", "quantidade_desperdiçada_kg", "desperdicio_bool"
            ]
            df_vendas = df_vendas[colunas_contrato_silver]

            df_vendas["ano"], df_vendas["mes"], df_vendas["dia"] = str(ano), str(mes), str(dia)

            # -------------------------------------------------------------------------
            # FASE 8: VALIDAÇÃO DO CONTRATO DO PANDERA E GRAVAÇÃO DA FATO
            # -------------------------------------------------------------------------
            schema_vendas = pa.DataFrameSchema({
                "id_venda": Column(pa.Int, coerce=True, nullable=False),
                "id_cliente": Column(pa.Int, coerce=True, nullable=False),
                "nome_cliente": Column(pa.String, nullable=False),
                "id_prato": Column(pa.Int, coerce=True, nullable=False),
                "prato_comprado": Column(pa.String, nullable=False),
                "data_venda": Column(pa.String, Check.str_matches(r"^\d{2}/\d{2}/\d{4}$"), nullable=False),
                "valor_gasto": Column(pa.Float, Check.greater_than(0.0), coerce=True),
                "alimento_desperdiçado": Column(pa.String, nullable=False),
                "quantidade_desperdiçada_kg": Column(pa.Float, Check.greater_than_or_equal_to(0.0), coerce=True),
                "desperdicio_bool": Column(pa.Bool, coerce=True, nullable=False)
            })
            schema_vendas.validate(df_vendas, inplace=True)

            wr.s3.to_parquet(
                df=df_vendas, path=f"s3://{self.bucket_silver}/prata/vendas_semanais/", dataset=True,
                database=self.database_silver, table="vendas_semanais",
                partition_cols=["ano", "mes", "dia"], mode="overwrite_partitions", boto3_session=self.session
            )
            return df_vendas
        except Exception as e:
            self.logger.error(f"❌ Erro na esteira de vendas: {e}")
            raise e

# %% ==========================================================================
# SESSÃO 5: GATILHO PRINCIPAL (ORQUESTRADOR DINÂMICO DE PRODUÇÃO E TESTES)
# ==========================================================================
if __name__ == "__main__":
    # 🕹️ CONTROLADOR DE AMBIENTE INTERATIVO
    # MODO_TESTE = False -> Modo Produção Automatizado (Roda ontem dinamicamente para o GitHub Actions)
    # MODO_TESTE = True  -> Modo de Depuração Jupyter (Roda o backfill das datas históricas fixas abaixo)
    MODO_TESTE = False 
    
    if MODO_TESTE:
        print("🧪 [MODO TESTE] Executando rotina interativa de Backfill para lotes históricos...")
        datas_execucao = [
            datetime(2026, 5, 29),
            datetime(2026, 6, 1),
            datetime(2026, 6, 8)
        ]
    else:
        print("⏳ [PRODUÇÃO] Inicializando gatilho dinâmico via Cron (GitHub Actions)...")
        # Fallback automático: captura ontem (datetime.now() - 1 dia)
        datas_execucao = [datetime.now() - timedelta(days=1)]
        
    print("=" * 95)
    
    for lote_data in datas_execucao:
        print(f"🚀 Executando processamento integrado para a data de corte: {lote_data.strftime('%d/%m/%Y')}")
        pipeline_silver = SilverPipelineETL(data_execucao=lote_data)
        df_est_ok = pipeline_silver.processar_dados_estoque()
        df_ven_ok = pipeline_silver.processar_dados_vendas()
        
    print("\n" + "="*95 + "\n🏆 PIPELINE DA CAMADA SILVER PROCESSADO COM SUCESSO!")

# %% ==========================================================================
# SESSÃO 6: TESTE DO JUPYTER E VALIDAÇÃO ANALÍTICA (VISUALIZAÇÃO COMPLETA)
# ==========================================================================
# AFIRMAÇÃO: Sincronizando partições criadas no S3 e forçando a leitura analítica via consultas SQL no Amazon Athena.
load_dotenv(override=True)
database_silver = os.getenv("DATABASE_SILVER")
aws_region = os.getenv("AWS_REGION")

if aws_region:
    boto3.setup_default_session(region_name=aws_region)

print("\n🕵️‍♂️ [AUDITORIA DE GOVERNANÇA ATHENA] Executando MSCK Repair e conferência de tabelas...")
print("=" * 95)

if database_silver:
    # Sincroniza as partições no Glue Data Catalog
    wr.athena.start_query_execution(sql="MSCK REPAIR TABLE estoque_ingredientes;", database=database_silver)
    wr.athena.start_query_execution(sql="MSCK REPAIR TABLE vendas_semanais;", database=database_silver)
    wr.athena.start_query_execution(sql="MSCK REPAIR TABLE dicionario_pratos;", database=database_silver)
    wr.athena.start_query_execution(sql="MSCK REPAIR TABLE dicionario_clientes;", database=database_silver)
    
    # 1. Auditoria Visual: estoque_ingredientes
    print("\n🔬 1. TABELA FATO: estoque_ingredientes")
    try:
        df_aud_est = wr.athena.read_sql_query(sql="SELECT * FROM estoque_ingredientes", database=database_silver)
        print("👀 [HEAD]")
        IPython.display.display(df_aud_est.head(5))
        print(f"📊 Total de linhas no Estoque: {len(df_aud_est)}")
    except Exception as e:
        print(f"  ⚠️ Erro na auditoria do estoque: {e}")
        
    # 2. Auditoria Visual: vendas_semanais
    print("\n" + "-"*95 + "\n🔬 2. TABELA FATO: vendas_semanais (Sem colunas lixo ou obsoletas)")
    try:
        df_aud_ven = wr.athena.read_sql_query(sql="SELECT * FROM vendas_semanais", database=database_silver)
        print("👀 [HEAD]")
        IPython.display.display(df_aud_ven.head(5))
        print(f"📊 Total de linhas em Vendas: {len(df_aud_ven)}")
    except Exception as e:
        print(f"  ⚠️ Erro na auditoria de vendas: {e}")

    # 3. Auditoria Visual: Tabelas de Dimensões Enviadas
    print("\n" + "-"*95 + "\n🔬 3. TABELAS DE DIMENSÕES (GRAVADAS EM PARQUET NA SILVER)")
    try:
        df_aud_pratos = wr.athena.read_sql_query(sql="SELECT * FROM dicionario_pratos", database=database_silver)
        df_aud_clientes = wr.athena.read_sql_query(sql="SELECT * FROM dicionario_clientes", database=database_silver)
        print(f"📋 Dicionário Pratos (Tamanho: {len(df_aud_pratos)}):")
        IPython.display.display(df_aud_pratos.head(3))
        print(f"📋 Dicionário Clientes (Tamanho: {len(df_aud_clientes)}):")
        IPython.display.display(df_aud_clientes.head(3))
    except Exception as e:
        print(f"  ⚠️ Erro na auditoria das tabelas de dimensões: {e}")
# %%
