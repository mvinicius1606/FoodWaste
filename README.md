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

2. [Processo de Ingestão](#)
   * [2.1. Diagrama da Arquitetura de Ingestão](#11-diagrama-da-arquitetura-de-ingestão)
   * [2.2. API Mockaroo](#12-api-mockaroo)
   *



---
## 1. 🏗️ Arquitetura Medalhão, AWS e Estrutura do Data Lake

O coração da estratégia de dados deste projeto está estruturado na **Arquitetura Medalhão**. Essa abordagem organiza o **Data Lake** no Amazon S3 em três camadas lógicas de maturidade. Em vez de misturar arquivos brutos com relatórios finais, os dados passam por uma esteira de evolução contínua, dividida em 3 etapas:

* **🟫 Camada Bronze (Ingestão):** É a porta de entrada do Data Lake. Aqui, os dados brutos e semiestruturados (arquivos XML de vendas e JSON de estoque) são armazenados semanalmente via pipeline de automatização da ingestão, sem nenhuma alteração. Isso garante o histórico contínuo e a rastreabilidade da origem.
* **⬜ Camada Silver (ETL e Qualidade):** É a camada de confiança e governança. O pipeline limpa as tabelas, remove colunas inúteis e aplica a **Âncora da Verdade** (Menu), e aplica o sistema de **Qualidade de Dados** com a biblioteca pandera, para garantir a consistência das receitas. Todos os dados são salvos em formato Parquet — que é altamente compactado, economiza espaço e acelera as consultas no Athena.
* **🟨 Camada Gold (Data Marts):** É a camada de inteligência de negócios. Os dados limpos da Silver são transformados em visões agregadas, prontas para alimentar ferramentas de relatórios (BI). O projeto separa essa camada em dois focos analíticos principais: o **Data Mart de Vendas** e o **Data Mart de Desperdícios**.

---

### 1.1💰 Controle de Custos e Escolhas Tecnológicas (FinOps)

Para criar um projeto eficiente e com custo quase zero, adotamos uma arquitetura focada estritamente em armazenamento (*storage-first*). Em vez de ligar servidores caros que cobram por hora ou clusters pesados de processamento que ficariam ociosos, o projeto utiliza uma abordagem totalmente inteligente:

* **Armazenamento Único e Barato:** Utilizamos apenas o **Amazon S3** para hospedar toda a estrutura das nossas medalhas (Bronze, Silver e Gold), pagando centavos apenas pelo espaço físico dos arquivos.
* **Programação Direta e Sem Servidores:** Toda a lógica de extração e transformação foi escrita em Python puro, utilizando a integração entre as bibliotecas **Boto3** (o braço oficial da AWS) e **AWS Wrangler (awswrangler)**. 

Essa combinação fantástica permite ler os arquivos do S3, processar as regras de qualidade em memória e atualizar o catálogo de tabelas do Athena de forma rápida e direta. O custo de computação só existe durante os segundos em que o script roda, tornando o ecossistema incrivelmente econômico e escalável para o portfólio..

---

### 1.2. 💰 Estratégia de Controle de Custos (FinOps)
Visando a máxima economia de infraestrutura, o projeto adota uma arquitetura orientada a armazenamento (*storage-first*). Em vez de manter servidores ativos 24/7 ou clusters caros de processamento, utilizamos apenas o **Amazon S3** como repositório central de armazenamento das medalhas. 

Toda a lógica de programação e processamento é executada de forma leve e otimizada através da integração direta via código Python com as bibliotecas **Boto3** (SDK oficial da AWS) e **AWS Wrangler (awswrangler)**. Essa escolha permite interagir diretamente com o S3, o AWS Glue Data Catalog e o Amazon Athena sem gerar custos fixos de infraestrutura pesada.

---

## 1.2 📈 AWS CloudWatch: Central de Logging

A monitoração contínua é essencial para garantir a saúde do pipeline. O projeto utiliza o módulo `logging` do Python integrado ao **AWS CloudWatch** para registrar de forma transparente o comportamento do ecossistema em todas as 3 etapas:

* **Na Ingestão (Bronze):** Registra o sucesso da conexão com os simuladores, falhas na geração de payloads da API, o volume de arquivos recebidos e a confirmação de upload dos arquivos brutos no S3.
* **No ETL (Silver):** Registra as quebras de contrato de dados capturadas pelo Pandera, o andamento das limpezas de strings, os acionamentos da Âncora da Verdade para preenchimento de dados nulos e o tempo de reescrita das partições Parquet.
* **Nos Data Marts (Gold):** Registra o sucesso do cálculo das métricas agregadas, falhas em cruzamentos de BI e a atualização final das tabelas analíticas prontas para os dashboards.

---

## 1.3 🐳 Isolamento Ambiental com Docker

Para assegurar que o projeto rode perfeitamente em qualquer ambiente — inclusive na automação do GitHub Actions — toda a arquitetura foi conteinerizada utilizando o **Docker**, dividida estrategicamente da seguinte forma:

* **Etapa de Ingestão (Bronze):** Está dockerizada de forma **isolada**. Por se tratar de um microsserviço que lida com simulação externa e chamadas de API com agendamentos próprios, ela roda de maneira 100% independente, sem interferir no restante do sistema.
* **Etapas Silver e Gold:** Estão dockerizadas **em conjunto** dentro de um único container. Como a camada Gold depende diretamente do sucesso imediato das validações da camada Silver, ambas compartilham o mesmo ambiente de engenharia (Pandas, Pandera e AWS Wrangler) e são orquestradas em sequência a partir de um único arquivo gatilho: o **`main.py`**.

---

## 🔌 2. Dados Simulados e Mockaroo.

Para simular o funcionamento real de um restaurante sem depender de dados confidenciais, o projeto utiliza a API do **Mockaroo** via URL para gerar conjuntos de dados sintéticos (dados simulados) de alta fidelidade. 

O pipeline de ingestão foi desenvolvido utilizando o **FastAPI** e está programado para rodar semanalmente. Quando acionado, ele faz as requisições para a API do Mockaroo e gera automaticamente os seguintes arquivos:

* **Tabela `estoque_ingredientes`:** Gerada no formato **JSON**, simulando as compras e entradas de insumos no estoque do restaurante.
* **Tabela `vendas_semanais`:** Gerada no formato **XML**, emulando o histórico de pratos vendidos e os registros de desperdício dos clientes.

Todo o código de configuração e as regras dos esquemas utilizados para criar esses dados estão organizados na pasta: [src/ingestao/mockaroo](src/ingestao/mockaroo).

---

### ⚓ 2.1. A Terceira Tabela: `tabela_menu.csv`

Além dos arquivos gerados semanalmente pela API, o ecossistema conta com uma terceira tabela fixa chamada **`tabela_menu.csv`**. 

Diferente das outras duas, esta tabela **não possui dados sujos e não sofre mudanças semanais**. Ela foi criada estrategicamente para funcionar como a nossa **Âncora da Verdade** (*Ground Truth*), servindo de guia estático para que o pipeline da camada Silver possa auditar, cruzar e corrigir qualquer informação inconsistente que venha das simulações.

---

### 2.2. Ingestão de Dados Anômalos ("Dados Sujos")
Alinhado às melhores práticas de Engenharia de Dados e visando estressar as etapas subsequentes de tratamento (ETL) e os modelos de Machine Learning, os esquemas foram configurados intencionalmente para gerar dados sujos e inconsistentes.

Essa estratégia metodológica introduz artificialmente na carga:

- Valores nulos (null) e campos ausentes em colunas cruciais (como registros flutuantes de desperdicio_clientes).

- Outliers e discrepâncias volumétricas (ex: registros de consumo zerados ou picos impossíveis de vendas em horários de fechamento).

- Inconsistências de formatação de strings e carimbos de data/hora desalinhados.

Essa "sujeira" programada emula os ruídos típicos enfrentados em ambientes de produção reais, justificando cientificamente a necessidade de uma camada de refino robusta no Data Lake.

---
## Tabelas da Camada Bronze:

---

### 📋  Tabela de Referência: `tabela_menu.csv` (Origem CSV)

Esta tabela funciona como a nossa **Âncora da Verdade** na memória do Python. Ela dita as regras de negócio e os limites físicos que os dados das vendas e do estoque devem respeitar.

| Coluna | Tipo de Dado (Origem) | Papel no Pipeline / Regra de Qualidade |
| :--- | :--- | :--- |
| `id_prato` | Numérico (`int`) | Chave primária utilizada para corrigir e vincular as vendas na Silver. |
| `prato` | Texto (`string`) | Nome oficial do cardápio utilizado para limpar as oscilações da Bronze. |
| `ingrediente` | Texto (`string`) | Lista de insumos reais que compõem a receita do prato (Formato Longo). |
| `qtd_base_kg` | Decimal (`float`) | Peso máximo padrão da porção servida. Usado como teto físico (*clamping*). |
| `preço_venda` | Texto (`string`) | Valor financeiro oficial do prato. Substitui os valores gerados na simulação. |

---

### 🛒 2. Tabela Bruta: `vendas_semanais` (Camada Bronze - Origem XML)

Dados originais extraídos dos arquivos XML. Apresentam alto volume de dados duplicados devido ao parser recursivo e inconsistências de nomenclatura da API.

| Tag / Campo XML | Tipo de Dado Bruto | Estado Atual / Problema Identificado na Bronze |
| :--- | :--- | :--- |
| `id_venda` | Texto (`string`) | Código identificador da transação (precisa de conversão para inteiro). |
| `id_cliente` | Texto (`string`) | Identificador do cliente (apresenta lacunas e valores nulos). |
| `nome_cliente` | Texto (`string`) | Nome do comprador (apresenta valores nulos ou desconectados do ID). |
| `id_prato_fk` | Texto (`string`) | O código do prato veio com o sufixo `_fk` (será renomeado e corrigido). |
| `prato_comprado` | Texto (`string`) | Nome do prato gravado (apresenta erros de digitação e variações). |
| `data_venda` | Texto (`string`) | Data do registro gravada em múltiplos formatos de texto. |
| `valor_gasto` | Texto (`string`) | Preço da venda contendo símbolos de moeda (ex: "R$ 45,00"). |
| `desperdicio_bool` | Texto (`string`) | Indicador lógico de desperdício gravado como texto ("true"/"false"). |
| `desperdicio_clientes` | Texto (`string`) | Nome do ingrediente deixado no prato (pluralizado e com nomes inválidos). |
| `quantidade_desperdiçada_g` | Texto (`string`) | Peso do desperdício registrado em gramas (ex: "150g"). |
| `_master_venda` | Nó Interno / Objeto | Bloco estrutural que carrega as tags redundantes `id`, `n`, `p` que devem ser deletadas. |

---

### 📦 3. Tabela Bruta: `estoque_ingredientes` (Camada Bronze - Origem JSON)

Dados originais extraídos dos arquivos JSON. A estrutura horizontalizada oculta as informações principais e mistura números com caracteres textuais.

| Campo JSON | Tipo de Dado Bruto | Estado Atual / Problema Identificado na Bronze |
| :--- | :--- | :--- |
| `id_estoque` | Texto / Inteiro | Código de controle interno do simulador (lixo estrutural para descarte). |
| `id` | Texto / Inteiro | Identificador redundante gerado na origem (lixo estrutural para descarte). |
| `n` | Texto / Inteiro | Metadado de numeração desnecessário (lixo estrutural para descarte). |
| `cat` | Texto (`string`) | Abreviação para a categoria do produto (ex: "hort", "carn"). Será expandida. |
| `data_compra` | Texto (`string`) | Data de entrada do insumo registrada como texto puro. |
| `quantidade_estoque` | Texto (`string`) | Peso volumétrico contendo a unidade de medida colada (ex: "15kg"). |
| `preço_unidade` | Texto (`string`) | Custo unitário do ingrediente contendo o caractere monetário "R$". |
| `_master_ing` | Objeto Aninhado | Estrutura em array que esconde as colunas reais `id_ingrediente` e `nome_ingrediente`. |

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



# ⚙️ ETL - Camada Silver

O processo de ETL (Extração, Transformação e Carregamento) para a camada Silver é o coração do projeto **FoodWaste**. Nesta etapa, o pipeline atua como um filtro de governança: ele captura os dados brutos e instáveis armazenados na camada **Bronze** e os transforma em tabelas limpas, padronizadas e otimizadas no formato Parquet, prontas para análises rápidas e seguras.

---

## 📊 Análise Preditiva e Escolha Tecnológica

Em vez de utilizarmos apenas as ferramentas visuais padronizadas do AWS Glue, fizemos a escolha estratégica de desenvolver o pipeline utilizando o **AWS Wrangler (awswrangler)**. Essa decisão foi fundamental para viabilizar as futuras etapas de análise preditiva do projeto. 

O AWS Wrangler permitiu unir a flexibilidade do Pandas (para processar regras de negócio complexas diretamente na memória) com a escala da nuvem AWS. Com essa abordagem, conseguimos criar validações cruzadas e cruzamentos tridimensionais de dados em frações de segundo — operações personalizadas que seriam extremamente difíceis, engessadas ou caras de se implementar através de caixas visuais comuns do AWS Glue.

### ⚠️ Problemas Encontrados na Camada Bronze:
* **Tabela `estoque_ingredientes` (Origem JSON):** Os dados vinham em um formato horizontal incômodo (arrays aninhados), o que dificultava a leitura visual. Além disso, os pesos vinham como texto misturados com letras (ex: "10kg") e os valores financeiros traziam o símbolo de moeda ("R$"), impedindo cálculos matemáticos diretos.
* **Tabela `vendas_semanais` (Origem XML):** Sofria com um aumento falso no volume de dados. O leitor padrão do XML confundia os ingredientes das receitas com novas vendas, duplicando as linhas do arquivo. Para piorar, a API simuladora apresentava oscilações de nomes (tags ora no plural, ora no singular) e gerava registros com IDs de clientes vazios ou desconectados de seus nomes originais.

---

## 🛠️ Soluções e Transformações Aplicadas

Para construir um pipeline resiliente e à prova de falhas, aplicamos as seguintes normas e tratamentos de engenharia de dados:

* **⚡ Mecanismo de Âncora da Verdade:** Transformamos a tabela de menu em dicionários rápidos na memória (Tabelas Hash). O pipeline consulta essa lista instantaneamente para corrigir códigos de pratos errados e garantir que o nome do prato na Silver seja exatamente o do cardápio oficial.
* **🔒 Blindagem Financeira:** Ignoramos os valores de venda gerados de forma aleatória na simulação. O pipeline faz um cruzamento em tempo real e insere na coluna `valor_gasto` o preço oficial tabelado do menu.
* **⚖️ Auditoria de Receita e Trava Física (*Clamping*):** Criamos uma lógica que checa se o ingrediente desperdiçado realmente faz parte da receita daquele prato. O peso é convertido automaticamente de gramas para quilos e passa por uma trava de segurança: a quantidade jogada fora nunca pode ser maior do que o peso total da porção servida no restaurante.
* **🏢 Bunker de Clientes:** Desenvolvemos uma inteligência para mapear IDs e nomes de clientes de forma bidirecional. Se faltar o nome, o ID recupera; se o ID vier zerado, o nome localiza o código correto. Todos os nomes são padronizados com as iniciais maiúsculas (*Title Case*).
* **🧹 Faxina Estrutural:** Eliminamos todas as colunas redundantes, restos de tags obsoletas e lixos gerados pelo simulador (`id_prato_fk`, `desperdicio_clientes`, `id`, `n`, `p`), deixando apenas o que importa para o negócio.

### 🧰 Ferramentas Utilizadas (Destaques para o Portfólio):
* **Linguagem e Manipulação de Dados:** Python 3.x e Pandas (processamento matricial e limpeza de tabelas).
* **Controle de Qualidade de Dados:** Pandera (framework para validação estrita de esquemas e contratos de dados em tempo de execução).
* **Conexão e Integração com a Nuvem:** AWS Wrangler (`awswrangler`), Boto3 (SDK oficial da AWS) e ElementTree (para leitura direcionada e precisa de arquivos XML).
* **Infraestrutura Cloud:** Amazon S3 (armazenamento de arquivos Parquet), AWS Glue Data Catalog (catálogo e governança de metadados) e Amazon Athena (mecanismo de consulta servless utilizando SQL padrão).

---

## 💎 Tabelas Silver Finais

Ao final do processamento, limpamos os metadados antigos para garantir que o Amazon Athena exiba apenas o modelo novo e otimizado. O resultado da modelagem dividiu-se em tabelas de **Fato** (histórico e métricas) e **Dimensão** (cadastros de referência):

### 📅 1. Visão Geral do Data Lake (Camada Silver)

| Nome da Tabela | Tipo de Tabela | Descrição Analítica | Formato de Armazenamento | Particionamento Físico |
| :--- | :--- | :--- | :--- | :--- |
| **`vendas_semanais`** | Fato | Registro histórico de transações de vendas com auditoria tridimensional de desperdício. | Parquet (Altamente Comprimido) | `ano`, `mes`, `dia` |
| **`estoque_ingredientes`** | Fato | Movimentações de insumos comprados, preços unitários e pesos totalmente achatados. | Parquet (Altamente Comprimido) | `ano`, `mes`, `dia` |
| **`dicionario_pratos`** | Dimensão | Catálogo mestre e estável de pratos oficiais e preços de venda vigentes do cardápio. | Parquet (Tabela Estática) | Não Particionado |
| **`dicionario_clientes`** | Dimensão | Cadastro consolidado de clientes gerado de forma dinâmica a partir do histórico de-para. | Parquet (Tabela Estática) | Não Particionado |

---

### 🧬 2. Estrutura de Colunas e Contratos de Dados (Esquemas Athena)

Para garantir a transparência do portfólio, abaixo estão os campos exatos salvos em cada tabela após passar pelo controle de qualidade do **Pandera**:

#### 🛒 Tabela: `vendas_semanais` (10 Colunas Oficiais)
| Coluna | Tipo de Dado | Regra de Data Quality Aplicada |
| :--- | :--- | :--- |
| `id_venda` | `int64` | Chave primária limpa e convertida em valor absoluto. |
| `id_cliente` | `int64` | Código do cliente recuperado dinamicamente via Tabela Hash. |
| `nome_cliente` | `string` | Nome higienizado em *Title Case* (Iniciais Maiúsculas). |
| `id_prato` | `int64` | Código do prato corrigido com base na âncora do menu. |
| `prato_comprado` | `string` | Descrição exata herdada do cardápio oficial. |
| `data_venda` | `string` | Data padronizada sob a máscara regulatória `dd/mm/AAAA`. |
| `valor_gasto` | `float64` | Preço de venda oficial injetado (ignora alucinações da origem). |
| `alimento_desperdiçado` | `string` | Insumo validado (substitui lixos que não pertencem à receita). |
| `quantidade_desperdiçada_kg` | `float64` | Convertido para quilos e limitado ao teto máximo da receita (*clamping*). |
| `desperdicio_bool` | `boolean` | Flag lógica nativa do Python (`True`/`False`). |

#### 📦 Tabela: `estoque_ingredientes`
| Coluna | Tipo de Dado | Regra de Data Quality Aplicada |
| :--- | :--- | :--- |
| `id_ingrediente` | `int64` | Código identificador do insumo limpo e tipado. |
| `nome_ingrediente` | `string` | Nome do ingrediente padronizado em *Title Case*. |
| `data_compra` | `string` | Data de entrada tratada no formato padrão `dd/mm/AAAA`. |
| `quantidade_estoque` | `float64` | Peso líquido limpo de caracteres textuais (ex: remove o "kg"). |
| `preço_unidade` | `float64` | Valor financeiro puro extraído (ex: remove o "R$"). |
| `categoria` | `string` | Agrupamento mercadológico tratado em *Title Case*. |

#### 🍽️ Tabela Dimensão: `dicionario_pratos`
| Coluna | Tipo de Dado | Função no Modelo |
| :--- | :--- | :--- |
| `id_prato` | `int64` | Chave substituta para relacionamento com a Fato. |
| `prato` | `string` | Nome de exibição oficial do prato no painel de BI. |
| `preço_venda` | `float64` | Preço padrão utilizado para auditoria de receita na Gold. |

#### 👥 Tabela Dimensão: `dicionario_clientes`
| Coluna | Tipo de Dado | Função no Modelo |
| :--- | :--- | :--- |
| `id_cliente` | `int64` | Identificador único do consumidor mapeado no histórico. |
| `nome_cliente` | `string` | Nome completo limpo do cliente para cruzamento cadastral. |