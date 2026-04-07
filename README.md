# FoodWaste — Monitoramento e Prevenção de Desperdício Alimentar

O **FoodWaste** é uma solução de inteligência de dados ponta-a-ponta projetada para enfrentar o desafio do desperdício de alimentos em ambientes comerciais. O projeto realiza a ingestão de dados de vendas de forma autônoma para identificar padrões de consumo, prever sobras via Machine Learning e gerar recomendações operacionais de alto impacto.

Esta arquitetura foi projetada para operar de forma **100% automatizada**, simulando um ambiente real de produção com um histórico de **3 meses** de dados sintéticos de alta fidelidade.

---

## 🧩 Necessidades e Objetivos

* **Aperfeiçoamento Profissional:** Consolidação de conhecimentos avançados em **Engenharia de Dados** e **MLOps**, integrando Python, AWS, Docker e pipelines de CI/CD.
* **Sustentabilidade (ESG):** Redução do desperdício alimentar por meio de previsões de demanda precisas, otimizando estoques e compras de insumos.
* **Eficiência Financeira:** Geração de insights para tomadas de decisão que minimizam custos operacionais e aumentam a rentabilidade.

---

## 📌 Sumário

1. [Diagrama da Arquitetura](#-diagrama-da-arquitetura)
2. [Processo de Ingestão e Automação](#-processo-de-ingestão-e-automação)
3. [Estrutura do Data Lake (S3)](#-estrutura-do-data-lake-s3)
4. [Processamento e Refino (AWS Glue)](#-processamento-e-refino-aws-glue)
5. [Data Marts e Machine Learning](#-data-marts-e-machine-learning)
6. [Automação e CI/CD](#-automação-e-cicd)
7. [Como Executar](#-como-executar-localmente-via-docker)

---

## 📐 Diagrama da Arquitetura

Aqui está o fluxo lógico da solução, desde a geração do dado até a predição final:

> **[INSIRA O LINK DA SUA IMAGEM OU DIAGRAMA AQUI]**
> *Exemplo: Mockaroo -> FastAPI (Docker) -> S3 -> Glue -> Random Forest -> S3 Gold.*

---

## ⚙️ Processo de Ingestão e Automação

O pipeline de dados inicia com a geração de dados sintéticos que mimetizam um cenário real de restaurante:

* **Fonte de Dados:** Integração com a **API do Mockaroo** para gerar datasets de vendas fictícias.
* **Orquestração com FastAPI:** Criamos um microsserviço que automatiza o disparo dos dados. Ele está configurado para gerar e lançar **1000 novas vendas toda segunda-feira às 09:00**, durante um ciclo de **3 meses**.
* **ETL de Adequação (Pandas):** Antes do carregamento, o script realiza um tratamento rápido para garantir a tipagem de datas, renomeação de colunas e integridade dos dados.
* **Tecnologias:** O serviço de ingestão roda sobre **Docker** e possui um sistema de **Logging** detalhado para rastreabilidade de cada lote enviado.

---

## 🗄️ Estrutura do Data Lake (S3)

Os dados são organizados no Amazon S3 buscando o máximo de correlação entre as entidades:

1.  **Vendas (Bronze/Raw):** Recebe os lotes semanais da FastAPI.
2.  **Menu (Static):** Tabela pequena e fixa contendo a relação de pratos e preços.
3.  **Ingredientes (Monthly):** Tabela de insumos atualizada mensalmente (seguindo o mesmo processo de automação das vendas) para refletir variações de estoque e custo.

---

## ☁️ Processamento e Refino (AWS Glue)

Para transformar dados brutos em insights, utilizamos o ecossistema serverless da AWS:

* **AWS Crawler:** Identifica automaticamente novos arquivos no S3, cataloga o schema e atualiza o Data Catalog.
* **AWS Glue Jobs:** Scripts Python/Spark que unem as tabelas de vendas, menu e ingredientes.
* **Automação:** O processo é totalmente automatizado, onde os dados são limpos, tipados e devolvidos ao S3 em uma pasta de **dados tratados (camada Gold)**.

---

## 🧠 Data Marts e Machine Learning

Com os dados refinados, criamos dois **Data Marts** específicos para análise:

1.  **Data Mart de Vendas:** Focado em tendências comerciais e performance de produtos.
2.  **Data Mart de Desperdício:** Cruza o consumo real com a saída de estoque para identificar perdas.

### Predição com Random Forest
Utilizamos o algoritmo **Random Forest** para automatizar as análises preditivas:
* **Prevenção de Desperdício:** Identifica proativamente quais insumos correm risco de sobra com base na demanda histórica.
* **Perspectiva de Vendas:** Gera previsões de volume para otimizar a compra de ingredientes na semana seguinte.

---

## 🚀 Automação e CI/CD

Para garantir a portabilidade, implementamos uma esteira de **Integração e Entrega Contínua**:

1.  **Conteinerização:** Todo o ambiente de ingestão e predição é isolado em containers Docker.
2.  **GitHub Actions:**
    * **CI:** Validação de código e testes unitários a cada push.
    * **Build:** Geração da imagem e push para o **Amazon ECR**.
    * **CD:** Deploy automático para execução serverless no **AWS Fargate**.

---

## 📊 Observabilidade

* **Logging:** Centralização de logs de execução e erros no **Amazon CloudWatch**, permitindo o monitoramento de cada etapa do pipeline (FastAPI, Glue e ML).

---

## 🛠️ Como Executar (Localmente via Docker)

Caso deseje replicar o ambiente de ingestão/análise localmente:

```bash
# 1. Clone o repositório
git clone [https://github.com/seu-usuario/foodwaste.git](https://github.com/seu-usuario/foodwaste.git)

# 2. Construa a imagem Docker
docker build -t foodwaste-app .

# 3. Execute o container (certifique-se de configurar as variáveis de ambiente)
docker run --env-file .env foodwaste-app
