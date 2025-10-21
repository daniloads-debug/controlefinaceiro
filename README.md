# 💰 Sistema de Controle Financeiro Pessoal

Um sistema completo para controle de gastos mensais com projeção anual e análise avançada de dados financeiros.

## 🚀 Funcionalidades

### 📊 Dashboard Interativo
- **Métricas em tempo real**: Receitas, despesas, saldo e taxa de poupança
- **Score financeiro**: Avaliação automática da saúde financeira
- **Gráficos dinâmicos**: Distribuição de gastos e tendências mensais
- **Alertas inteligentes**: Detecção automática de gastos anômalos

### 💳 Gestão de Transações
- **Entrada simplificada**: Interface intuitiva para registro de receitas e despesas
- **Categorização automática**: Sistema inteligente de classificação
- **Histórico completo**: Visualização e filtros avançados
- **Validação de dados**: Controles para garantir integridade das informações

### 🔮 Análises Preditivas
- **Projeção anual**: Algoritmos de machine learning para previsão de gastos
- **Análise de tendências**: Identificação de padrões sazonais
- **Detecção de anomalias**: Alertas para gastos fora do padrão
- **Insights automáticos**: Recomendações baseadas em dados

### 📈 Relatórios Avançados
- **Exportação Excel**: Relatórios detalhados com gráficos
- **Relatórios PDF**: Documentos profissionais para análise
- **Análise por categoria**: Breakdown detalhado de gastos
- **Comparativos temporais**: Evolução mês a mês

## 🛠️ Tecnologias Utilizadas

- **Backend**: Python 3.8+
- **Interface**: Streamlit
- **Banco de Dados**: SQLite
- **Análise de Dados**: Pandas, NumPy
- **Machine Learning**: Scikit-learn
- **Visualização**: Plotly, Matplotlib
- **Relatórios**: ReportLab (PDF), OpenPyXL (Excel)

## 📦 Instalação

### Pré-requisitos
- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

### Passos para instalação

1. **Clone ou baixe o projeto**
   ```bash
   git clone <url-do-repositorio>
   cd trae-projeto-financeiro
   ```

2. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   ```

3. **Execute a aplicação**
   ```bash
   streamlit run app.py
   ```

4. **Acesse no navegador**
   - A aplicação será aberta automaticamente
   - Ou acesse: `http://localhost:8501`

## 🎯 Como Usar

### 1. Primeiro Acesso
- O sistema criará automaticamente o banco de dados
- Categorias padrão serão inseridas automaticamente
- Comece adicionando suas primeiras transações

### 2. Adicionando Transações
- Vá para "Adicionar Transação" no menu lateral
- Preencha: data, descrição, valor, categoria e tipo
- O sistema validará e salvará automaticamente

### 3. Visualizando o Dashboard
- Acesse "Dashboard" para ver métricas em tempo real
- Observe seu score financeiro e fatores de influência
- Analise gráficos de distribuição e tendências

### 4. Análises Avançadas
- Use "Análises" para insights detalhados por período
- Verifique alertas de gastos anômalos
- Analise top categorias de despesas

### 5. Projeções Futuras
- Acesse "Projeções" para ver previsões anuais
- Baseadas em seus dados históricos
- Úteis para planejamento financeiro

### 6. Relatórios
- Gere relatórios em PDF ou Excel
- Exporte dados para análise externa
- Compartilhe com consultores financeiros

## 📊 Estrutura do Projeto

```
projeto-financeiro/
├── app.py              # Aplicação principal Streamlit
├── database.py         # Gerenciamento do banco de dados
├── analytics.py        # Algoritmos de análise e ML
├── reports.py          # Geração de relatórios
├── requirements.txt    # Dependências do projeto
├── README.md          # Documentação
└── finance_data.db    # Banco de dados (criado automaticamente)
```

## 🔧 Configurações Avançadas

### Categorias Personalizadas
- Acesse "Configurações" no menu
- Adicione categorias específicas para seu perfil
- Configure orçamentos mensais por categoria

### Backup de Dados
- O arquivo `finance_data.db` contém todos os dados
- Faça backup regular deste arquivo
- Para restaurar, substitua o arquivo existente

### Personalização de Análises
- Modifique `analytics.py` para ajustar algoritmos
- Altere thresholds de detecção de anomalias
- Customize métricas do score financeiro

## 📈 Algoritmos de Análise

### 1. Projeção Anual
- **Método**: Regressão linear com dados históricos
- **Entrada**: Últimos 12 meses de transações
- **Saída**: Previsão mensal e anual por categoria

### 2. Detecção de Anomalias
- **Método**: Análise de desvio padrão (Z-score)
- **Threshold**: 2 desvios padrão (configurável)
- **Aplicação**: Identificação de gastos atípicos

### 3. Score Financeiro
- **Fatores**: Taxa de poupança (40%), diversificação (30%), consistência (30%)
- **Escala**: 0-100 pontos
- **Atualização**: Tempo real baseado no mês atual

### 4. Análise de Tendências
- **Período**: Últimos 12 meses
- **Métricas**: Crescimento/decrescimento por categoria
- **Visualização**: Gráficos de linha temporal

## 🚨 Alertas e Notificações

### Tipos de Alertas
1. **Gastos Anômalos**: Valores muito acima da média
2. **Orçamento Excedido**: Quando categoria ultrapassa meta
3. **Saldo Negativo**: Quando despesas > receitas
4. **Dados Insuficientes**: Para análises que precisam de histórico

### Configuração de Alertas
- Ajuste sensibilidade em `analytics.py`
- Modifique thresholds conforme necessário
- Personalize mensagens de alerta

## 📱 Interface do Usuário

### Design Responsivo
- Funciona em desktop, tablet e mobile
- Interface adaptativa com Streamlit
- Gráficos interativos com Plotly

### Navegação Intuitiva
- Menu lateral para acesso rápido
- Breadcrumbs para orientação
- Feedback visual para ações do usuário

## 🔒 Segurança e Privacidade

### Dados Locais
- Todos os dados ficam no seu computador
- Banco SQLite local (finance_data.db)
- Nenhuma informação enviada para servidores externos

### Backup Recomendado
- Faça backup regular do arquivo de banco
- Use serviços de nuvem para sincronização
- Mantenha cópias de segurança atualizadas

## 🤝 Contribuições

### Como Contribuir
1. Fork do projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

### Áreas para Melhoria
- Integração com bancos (Open Banking)
- App mobile nativo
- Sincronização em nuvem
- Mais algoritmos de ML
- Interface multilíngue

## 📞 Suporte

### Problemas Comuns
1. **Erro de dependências**: Verifique versão do Python
2. **Banco não criado**: Permissões de escrita na pasta
3. **Gráficos não aparecem**: Atualize navegador
4. **Performance lenta**: Muitas transações (otimize consultas)

### Logs e Debug
- Streamlit mostra erros no terminal
- Verifique arquivo de log para detalhes
- Use modo debug: `streamlit run app.py --logger.level=debug`

## 📄 Licença

Este projeto está sob licença MIT. Veja o arquivo LICENSE para detalhes.

## 🎉 Agradecimentos

- Comunidade Streamlit pela excelente framework
- Plotly pela biblioteca de visualização
- Scikit-learn pelos algoritmos de ML
- Todos os contribuidores e testadores

---

**Desenvolvido com ❤️ para ajudar no controle financeiro pessoal**