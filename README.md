# FoodWaste — Monitoramento e Prevenção de Desperdício Alimentar

O **FoodWaste** é uma solução de inteligência de dados ponta-a-ponta projetada para enfrentar o desafio do desperdício de alimentos em ambientes comerciais e de varejo. O projeto realiza a ingestão de dados de vendas de forma autônoma para identificar padrões de consumo, prever sobras via Machine Learning e gerar recomendações operacionais de alto impacto.

Esta arquitetura foi projetada para operar de forma **100% automatizada**, simulando um ambiente real de produção com um histórico de **2 meses** de dados sintéticos de alta fidelidade.

---

## 🧩 Necessidades e Objetivos

* **Portifólio profissional:** Demonstração e consolidação de conhecimentos avançados em **Engenharia de Dados** e **MLOps**, integrando Python, AWS (S3, Glue, Athena, CloudWatch), Docker e pipelines de CI/CD via GitHub Actions.
* **Sustentabilidade (ESG):** Redução do desperdício alimentar por meio de previsões de demanda precisas, otimizando estoques e compras de insumos.
* **Eficiência Financeira e Administrativa:** Geração de insights e relatórios com base em dados de vendas e estoque para tomadas de decisão que minimizam custos operacionais e aumentam a rentabilidade.

---
## 🛠️ Tecnologias e Plataformas Utilizadas

O ecossistema do **FoodWaste** foi construído integrando as ferramentas mais robustas do mercado de Engenharia de Dados e DevOps para garantir resiliência, escalabilidade e segurança.

### 💻 Stack Tecnológica

| Plataforma / Tecnologia | Logo | Aplicação no Projeto |
| :--- | :---: | :--- |
| **Python** | [![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/) | Linguagem base utilizada para a construção dos scripts de extração, tratamento de dados (`Pandas`), modelagem analítica e algoritmos de ML. |
| **FastAPI** | [![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/) | Criação dos endpoints da API de ingestão, documentação via Swagger e gerenciamento de tarefas assíncronas em segundo plano. |
| **Docker** | [![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/) | Conteinerização completa do microsserviço de ingestão, garantindo isolamento do ambiente e portabilidade absoluta para a nuvem. |
| **GitHub Actions** | [![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)](https://github.com/features/actions) | Mecanismo de CI/CD e Orquestração. Valida a sintaxe via linter (`Flake8`) a cada push e dispara a carga batch semanal de forma serverless via `Cron Schedule`. |
| **Amazon S3** | [![Amazon S3](https://img.shields.io/badge/Amazon_S3-569A31?style=for-the-badge&logo=amazon-s3&logoColor=white)](https://aws.amazon.com/s3/) | Repositório central do Data Lake. Armazena os dados brutos de forma particionada (camada Bronze) em formatos XML (Vendas) e JSON (Estoque). |
| **AWS Glue** | [![AWS Glue](https://img.shields.io/badge/AWS_Glue-232F3E?style=for-the-badge&logo=amazon-aws&logoColor=white)](https://aws.amazon.com/glue/) | Catálogo de metadados (`Glue Crawlers`) e execução dos Jobs Spark/Python para transformação, limpeza e refino dos dados brutos para a camada Gold. |
| **Amazon Athena** | [![Amazon Athena](https://img.shields.io/badge/Amazon_Athena-232F3E?style=for-the-badge&logo=amazon-aws&logoColor=white)](https://aws.amazon.com/athena/) | Serviço de consultas interativas que possibilita rodar queries SQL diretamente sobre o S3, consolidando os Data Marts de Vendas e Desperdício. |
| **Amazon CloudWatch** | [![CloudWatch](https://img.shields.io/badge/Amazon_CloudWatch-FF4F8B?style=for-the-badge&logo=amazon-cloudwatch&logoColor=white)](https://aws.amazon.com/cloudwatch/) | Centralização de logs e observabilidade em tempo real. Integrado nativamente ao pipeline de carga via biblioteca `watchtower`. |
| **Mockaroo API** | [![Mockaroo](https://img.shields.io/badge/Mockaroo_API-FF69B4?style=for-the-badge&logo=json&logoColor=white)](https://www.mockaroo.com/) | Serviço externo consumido para a geração contínua de dados sintéticos de alta fidelidade que emulam o fluxo de um restaurante real. |

---

## 📌 Sumário

1.0 [Processo de Ingestão e Automação](#-processo-de-ingestão-e-automação)
   * [Ingestão de Vendas (XML)](#ingestão-de-vendas-xml)
   * [Ingestão de Estoque de Ingredientes (JSON)](#ingestão-de-estoque-de-ingredientes-json)
3. [Estrutura do Data Lake (S3)](#-estrutura-do-data-lake-s3)
4. [Processamento e Refino (AWS Glue)](#-processamento-e-refino-aws-glue)
5. [Data Marts e Machine Learning](#-data-marts-e-machine-learning)
6. [Automação e CI/CD (GitHub Actions)](#-automação-e-cicd-github-actions)
   * [Gatilho por Código (CI)](#1-gatilho-por-código-ci)
   * [Gatilho por Tempo (Cron/Schedule)](#2-gatilho-por-tempo-cronschedule)
   * [Segurança com GitHub Secrets](#3-segurança-com-github-secrets)
7. [Observabilidade e Logs (CloudWatch)](#-observabilidade-e-logs-cloudwatch)
8. [Como Executar Localmente](#-como-executar-localmente)

---

## ⚙️1. Processo de Ingestão

Esta seção apresenta os aspectos metodológicos e estruturais da camada de ingestão de dados do projeto **FoodWaste**. O objetivo desta etapa é garantir a coleta automatizada, contínua e resiliente de dados sintéticos de alta fidelidade que emulam o fluxo operacional de um restaurante. Para isso, a arquitetura adota uma abordagem desacoplada que integra o desenvolvimento de microsserviços em Python, o isolamento ambiental via conteinerização e a orquestração de rotinas serverless para o provisionamento dos dados brutos no Data Lake, conforme detalhado nos subitens a seguir.

### 1.1. Diagrama da Arquitetura de Ingestão:


### 1.2. API Mockaroo e Modelagem de Dados Sintéticos
Para garantir o rigor metodológico e a padronização documental do projeto FoodWaste, detalham-se a seguir as estruturas das três tabelas geradas sinteticamente, mapeando os nomes exatos das colunas e as suas respectivas representações no modelo de negócios do restaurante:

#### Tabela 1: Vendas (`tabela_vendas_semanais`)
Esta tabela indexa o comportamento transacional dos clientes, registrando o volume de consumo e faturamento do estabelecimento.

| Nome da Coluna | Tipo de Dado | Descrição / Representação |
| :--- | :---: | :--- |
| `id_venda` | BigInt | Identificador único e incremental da transação comercial. |
| `data_hora` | Timestamp | Carimbo de data e horário em que o rodízio foi iniciado à mesa. |
| `modalidade_rodizio` | Varchar | Tipo de cardápio escolhido (ex: Executivo, Premium, Especial). |
| `quantidade_itens_pedidos` | Integer | Somatório total de peças ou pratos solicitados pela mesa ao longo da permanência. |
| `valor_total` | Decimal | Valor bruto faturado na mesa correspondente ao consumo e taxas associadas. |


#### Tabela 2: Estoque e Insumos (`tabela_estoque_ingredientes`)
Entidade responsável por rastrear o ciclo de vida, custos e a disponibilidade de matéria-prima dentro da cozinha operacional.

| Nome da Coluna | Tipo de Dado | Descrição / Representação |
| :--- | :---: | :--- |
| `id_lote` | BigInt | Chave primária identificadora do lote específico de insumo recebido. |
| `codigo_insumo` | Varchar | Código identificador da matéria-prima (ex: SALMAO_01, ARROZ_SHARI). |
| `quantidade_kg_ingressada` | Decimal | Volume total em quilogramas que deu entrada no estoque através do fornecedor. |
| `quantidade_disponivel` | Decimal | Saldo atualizado em quilogramas do insumo disponível para manipulação. |
| `custo_unitario` | Decimal | Custo por quilograma do insumo para fins de cálculo de prejuízo financeiro. |
| `data_validade` | Date | Data limite estabelecida para o consumo seguro do insumo. |


#### Tabela 3: Desperdício (`desperdicio`)
Mapeia quantitativamente as perdas geradas no estabelecimento, divididas entre desperdício operacional de cozinha e descarte excedente pós-consumo.

| Nome da Coluna | Tipo de Dado | Descrição / Representação |
| :--- | :---: | :--- |
| `id_desperdicio` | BigInt | Identificador único do registro de descarte ou perda. |
| `data_pesagem` | Timestamp | Data e momento exato em que a pesagem do descarte foi consolidada. |
| `tipo_descarte` | Varchar | Classificação da perda (ex: Sobra de Mesa, Validade Expirada, Erro de Preparo). |
| `peso_gramas` | Decimal | Massa total descartada mensurada em gramas. |
| `desperdicio_clientes` | Decimal | Métrica específica que quantifica o peso total de alimentos deixados intencionalmente nas mesas pelos consumidores. |
| `justificativa_perda` | Varchar | Campo descritivo detalhando o motivo do descarte para auditoria interna. |

### Ingestão de Dados Anômalos ("Dados Sujos")
Alinhado às melhores práticas de Engenharia de Dados e visando estressar as etapas subsequentes de tratamento (ETL) e os modelos de Machine Learning, os esquemas foram configurados intencionalmente para gerar dados sujos e inconsistentes.

Essa estratégia metodológica introduz artificialmente na carga:

- Valores nulos (null) e campos ausentes em colunas cruciais (como registros flutuantes de desperdicio_clientes).

- Outliers e discrepâncias volumétricas (ex: registros de consumo zerados ou picos impossíveis de vendas em horários de fechamento).

- Inconsistências de formatação de strings e carimbos de data/hora desalinhados.

Essa "sujeira" programada emula os ruídos típicos enfrentados em ambientes de produção reais, justificando cientificamente a necessidade de uma camada de refino robusta no Data Lake.

📁 Nota de Documentação: Os arquivos de configuração e esquemas em formato JSON que estruturam as três tabelas mapeadas no Mockaroo encontram-se armazenados no repositório no diretório: src/ingestao/mockaroo/

---

## 2. Desenvolvimento do Software e Arquitetura de Ingestão

Este capítulo detalha a implementação do ecossistema de software responsável pela captura, processamento, conteinerização e transporte dos dados. O sistema foi projetado sob os princípios de modularidade, alta disponibilidade e desacoplamento de serviços.

---

### 2.1. Programação Python e Lógica Core

O núcleo do pipeline foi desenvolvido em **Python 3.11**, utilizando uma abordagem híbrida de execução (*Dual Mode*). Essa estratégia permite que a mesma base de código sirva a dois propósitos distintos dentro do ciclo de vida da engenharia de dados:

1. **Modo Serverless Batch (CLI):** Executado via linha de comando por orquestradores de tempo, otimizando o uso de memória e evitando custos de ociosidade de computação.
2. **Modo Web API (FastAPI):** Fornece uma interface de rede para acionamentos manuais, auditorias e integrações em tempo real.

Essa flexibilidade foi alcançada através da implementação de travas estruturais idiomáticas (`if __name__ == "__main__":`), permitindo que as funções de coleta (`httpx`) e serialização (`dicttoxml`, `json`) sejam invocadas diretamente pela CLI do container sem a necessidade de inicializar o servidor HTTP Uvicorn durante a automação semanal.

---

### 2.2. Microsserviço com FastAPI e Documentação de Host

Para expor o pipeline a integrações externas e auditorias de dados, a biblioteca **FastAPI** foi adotada devido ao seu alto desempenho baseado em padrões abertos (`Asynchronous Server Gateway Interface - ASGI`).

* **Processamento Assíncrono:** As rotas de ingestão utilizam `BackgroundTasks`, permitindo que o cliente receba uma resposta HTTP 202 (Accepted) imediata, enquanto o script processa a requisição pesada à API do Mockaroo e faz o upload para o S3 em segundo plano.
* **Auto-Documentação:** A plataforma gera automaticamente a especificação OpenAPI e o painel de testes interativo (Swagger UI), o que simplifica a validação dos contratos de dados das três tabelas (`vendas`, `estoque_insumos`, `desperdicio`).

> 🖼️ **Interface de Documentação e Testes (Swagger UI)**
> ![Dashboard do Host FastAPI / Swagger UI](CADASTRAR_LINK_DA_IMAGEM_DO_SWAGGER_AQUI)
> *Figura 1: Endpoints do ecossistema FoodWaste expostos localmente via Uvicorn.*

---

### 2.3. Conteinerização com Docker

A reprodutibilidade do ambiente computacional e o isolamento de dependências foram garantidos através da criação de uma imagem customizada via **Docker**. Isso elimina o problema clássico de inconsistência entre o ambiente de desenvolvimento local e os *runners* serverless da nuvem (*environment drift*).

O `Dockerfile` foi estruturado seguindo as boas práticas de otimização de imagens:
* **Imagem Base:** Utilização do `python:3.11-slim` para mitigar a superfície de ataque e reduzir o tamanho final da imagem.
* **Camada de Dependências:** Instalação isolada do `requirements.txt` com limpeza automática de caches de pacotes (`pip cache purge`).
* **Injeção de Variáveis:** O container é parametrizado para ler de forma segura as credenciais contidas no arquivo `.env` (injetado localmente via `--env-file` ou remotamente via instanciamento dinâmico pelo GitHub Secrets).

> 🖼️ **Arquitetura de Isolamento do Container**
> ![Estrutura e Fluxo do Docker no Pipeline](CADASTRAR_LINK_DA_IMAGEM_DO_DOCKER_AQUI)
> *Figura 2: Empacotamento de dependências isoladas e o ciclo de execução do container.*

---

### 2.4. Subsistema de Logging, Telemetria e Envio para o Amazon S3

A fase final da ingestão consiste no transporte seguro e na geração de trilhas de auditoria para fins de observabilidade.

#### Ingestão de Dados Poliglota no Amazon S3
O script utiliza a SDK oficial da AWS para Python (`boto3`) para interagir com o Object Storage. O dado coletado passa por duas ramificações lógicas distintas:
* **Vendas:** O payload bruto recebido é transformado em uma string estruturada em **XML**, envelopada sob a tag raiz `<vendas>`, e enviada ao S3.
* **Estoque e Desperdício:** Os dados são mantidos e gravados no formato raw **JSON**, garantindo que o pipeline trate diferentes tipagens estruturais de arquivos.

O armazenamento é indexado utilizando **particionamento temporal** (`ano=YYYY/mes=MM/dia=DD/`), uma técnica científica que reduz o custo e o tempo de varredura (*scan*) das consultas executadas futuramente via Amazon Athena.

#### Telemetria Ativa com CloudWatch
Para monitorar a saúde do pipeline sem a necessidade de acessar os servidores, o componente de `logging` nativo do Python foi acoplado à biblioteca **Watchtower**. 

A cada ciclo de execução:
1. O sistema abre um stream de comunicação criptografado com o **Amazon CloudWatch**.
2. Eventos críticos (como códigos de status HTTP 200, falhas de timeout com o Mockaroo, contagem de registros injetados ou erros de chaves AWS) são transmitidos em tempo real para o grupo de logs `FoodWasteLogs`.
3. Isso estabelece uma arquitetura robusta de monitoramento, permitindo a criação futura de alertas automáticos para falhas operacionais na ingestão de dados.
