# FoodWaste — Monitoramento e Prevenção de Desperdício Alimentar

O **FoodWaste** é uma solução de inteligência de dados ponta-a-ponta projetada para enfrentar o desafio do desperdício de alimentos em ambientes comerciais. O projeto processa dados heterogêneos para identificar padrões de consumo, prever sobras via Machine Learning (PyTorch) e gerar recomendações operacionais de alto impacto.

Esta arquitetura foi projetada para operar de forma **100% automatizada**, permitindo uma análise histórica e preditiva contínua de **6 meses**, simulando um ambiente real de produção e escala.

---

## 🧩 Necessidades e Objetivos

* **Aperfeiçoamento Profissional:** Consolidação de conhecimentos avançados em **Engenharia de Dados** e **MLOps**, integrando Python, AWS, Docker e pipelines de CI/CD.
* **Sustentabilidade (ESG):** Redução do desperdício alimentar por meio de previsões de demanda precisas, otimizando estoques e compras de insumos.
* **Eficiência Financeira:** Geração de insights para tomadas de decisão que minimizam custos operacionais e aumentam a rentabilidade.

---

## ⚙️ Arquitetura e Fluxo de Dados

O projeto utiliza uma abordagem de **Data Lake** na AWS, estruturada em camadas para garantir a qualidade e a governança dos dados.

### 🏗️ Infraestrutura AWS
* **Ingestão (Bronze):** Dados sintéticos robustos gerados via **Mockaroo API** e ingeridos por um microsserviço em **FastAPI**.
* **Processamento (Silver):** **AWS Glue** para limpeza, tipagem e tratamento de dados heterogêneos (CSV, XLSX, JSON).
* **Consumo (Gold):** **AWS Athena** para consultas ad-hoc e criação de **Data Marts** (Vendas e Desperdício) em Python/Pandas.
* **Orquestração:** **Amazon EventBridge** agendando execuções diárias para garantir o fluxo contínuo por 6 meses.

---

## 🚀 Automação e CI/CD

Para garantir a portabilidade e a evolução do projeto, implementamos uma esteira de **Integração e Entrega Contínua (CI/CD)** via **GitHub Actions**:

1.  **Conteinerização (Docker):** Todo o ambiente de análise e o modelo de ML são isolados em containers Docker, garantindo que o código rode identicamente em qualquer ambiente.
2.  **Pipeline Automatizado:** * **CI:** Testes unitários e validação de código a cada *push*.
    * **Build:** Criação automática da imagem Docker e envio para o **Amazon ECR**.
    * **CD:** Deploy automático no **AWS Fargate** para execução serverless do pipeline.

---

## 🧠 Machine Learning e Predição

Utilizamos **PyTorch** para desenvolver um modelo preditivo capaz de:
* Prever o volume de desperdício diário com base no histórico de vendas.
* Identificar padrões sazonais (feriados, fins de semana e variações mensais).
* **Análise de 6 Meses:** Estudo do impacto financeiro acumulado e monitoramento de *Model Drift* (degradação do modelo ao longo do tempo).

---

## 📊 Observ
