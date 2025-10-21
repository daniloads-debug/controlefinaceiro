import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import numpy as np
import sqlite3

from database import FinanceDatabase
from analytics import FinanceAnalytics
from reports import ReportGenerator

# Configuração da página
st.set_page_config(
    page_title="Controle Financeiro Pessoal",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicialização do banco de dados
@st.cache_resource
def init_database():
    return FinanceDatabase()

@st.cache_resource
def init_analytics(_db):
    return FinanceAnalytics(_db)

# CSS customizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-card {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
    }
    .warning-card {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
    }
    .danger-card {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Inicializar banco e analytics
    db = init_database()
    analytics = init_analytics(db)
    
    # Header principal
    st.markdown('<h1 class="main-header">💰 Controle Financeiro Pessoal</h1>', unsafe_allow_html=True)
    
    # Sidebar para navegação
    st.sidebar.title("📊 Menu Principal")
    page = st.sidebar.selectbox(
        "Escolha uma opção:",
        ["Dashboard", "Adicionar Transação", "Histórico", "Análises", "Projeções", "Configurações"]
    )
    
    if page == "Dashboard":
        show_dashboard(db, analytics)
    elif page == "Adicionar Transação":
        show_add_transaction(db)
    elif page == "Histórico":
        show_history(db)
    elif page == "Análises":
        show_analytics(db, analytics)
    elif page == "Projeções":
        show_projections(db, analytics)
    elif page == "Configurações":
        show_settings(db)

def show_dashboard(db, analytics):
    st.header("📈 Dashboard Financeiro")
    
    # Métricas do mês atual
    current_date = datetime.now()
    current_month = current_date.month
    current_year = current_date.year
    
    insights = analytics.calculate_category_insights(current_year, current_month)
    
    if insights:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "💰 Receitas do Mês",
                f"R$ {insights['total_income']:,.2f}",
                delta=None
            )
        
        with col2:
            st.metric(
                "💸 Despesas do Mês",
                f"R$ {insights['total_expenses']:,.2f}",
                delta=None
            )
        
        with col3:
            balance_color = "normal" if insights['balance'] >= 0 else "inverse"
            st.metric(
                "⚖️ Saldo do Mês",
                f"R$ {insights['balance']:,.2f}",
                delta=None,
                delta_color=balance_color
            )
        
        with col4:
            st.metric(
                "📊 Taxa de Poupança",
                f"{insights['savings_rate']:.1f}%",
                delta=None
            )
        
        # Métricas de contas a pagar e receber
        st.subheader("💳 Contas a Pagar e Receber")
        
        # Buscar transações pendentes
        df = db.get_transactions()
        
        if not df.empty:
            # Verificar se as colunas necessárias existem
            if 'status' in df.columns and 'type' in df.columns:
                pending_transactions = df[df['status'] == 'pendente']
                pending_receivables = pending_transactions[pending_transactions['type'] == 'receita']['amount'].sum()
                pending_payables = pending_transactions[pending_transactions['type'] == 'despesa']['amount'].sum()
                
                # Transações em atraso
                today = pd.Timestamp.now()
                if 'due_date' in df.columns:
                    try:
                        df_temp = df.copy()
                        df_temp['due_date_parsed'] = pd.to_datetime(df_temp['due_date'], errors='coerce')
                        overdue_transactions = df_temp[
                            (df_temp['status'] == 'pendente') & 
                            (pd.notna(df_temp['due_date_parsed'])) & 
                            (df_temp['due_date_parsed'] < today)
                        ]
                        overdue_amount = overdue_transactions['amount'].sum()
                    except:
                        overdue_transactions = pd.DataFrame()
                        overdue_amount = 0
                else:
                    overdue_transactions = pd.DataFrame()
                    overdue_amount = 0
            else:
                pending_receivables = 0
                pending_payables = 0
                overdue_transactions = pd.DataFrame()
                overdue_amount = 0
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📥 A Receber", f"R$ {pending_receivables:,.2f}", 
                         help="Receitas pendentes")
            
            with col2:
                st.metric("📤 A Pagar", f"R$ {pending_payables:,.2f}", 
                         help="Despesas pendentes")
            
            with col3:
                st.metric("⚠️ Em Atraso", f"R$ {overdue_amount:,.2f}", 
                         delta=f"-{len(overdue_transactions)} transações" if len(overdue_transactions) > 0 else None,
                         delta_color="inverse")
            
            with col4:
                net_pending = pending_receivables - pending_payables
                st.metric("🔄 Saldo Pendente", f"R$ {net_pending:,.2f}")
            
            # Alertas de vencimento
            if not overdue_transactions.empty:
                st.error(f"🚨 Você tem {len(overdue_transactions)} transação(ões) em atraso!")
                
                with st.expander("Ver transações em atraso"):
                    for _, transaction in overdue_transactions.iterrows():
                        days_overdue = (today - pd.to_datetime(transaction['due_date']).date()).days
                        st.write(f"• **{transaction['description']}** - R$ {transaction['amount']:,.2f} "
                               f"(Venceu há {days_overdue} dias)")
            
            # Próximos vencimentos (próximos 7 dias)
            if 'status' in df.columns and 'due_date' in df.columns:
                try:
                    next_week = today + pd.Timedelta(days=7)
                    df_temp = df.copy()
                    df_temp['due_date_parsed'] = pd.to_datetime(df_temp['due_date'], errors='coerce')
                    upcoming_transactions = df_temp[
                        (df_temp['status'] == 'pendente') & 
                        (pd.notna(df_temp['due_date_parsed'])) & 
                        (df_temp['due_date_parsed'] >= today) &
                        (df_temp['due_date_parsed'] <= next_week)
                    ]
                except:
                    upcoming_transactions = pd.DataFrame()
            else:
                upcoming_transactions = pd.DataFrame()
            
            if not upcoming_transactions.empty:
                st.warning(f"📅 {len(upcoming_transactions)} transação(ões) vencem nos próximos 7 dias")
                
                with st.expander("Ver próximos vencimentos"):
                    for _, transaction in upcoming_transactions.iterrows():
                        days_until = (pd.to_datetime(transaction['due_date']).date() - today).days
                        st.write(f"• **{transaction['description']}** - R$ {transaction['amount']:,.2f} "
                               f"(Vence em {days_until} dias)")
        
        # Score financeiro
        score, factors = analytics.generate_financial_score()
        
        st.subheader("🎯 Score Financeiro")
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Gauge chart para o score
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = score,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Score"},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "yellow"},
                        {'range': [80, 100], 'color': "green"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            fig_gauge.update_layout(height=300)
            st.plotly_chart(fig_gauge, use_container_width=True)
        
        with col2:
            st.write("**Fatores que influenciam seu score:**")
            for factor in factors:
                st.write(f"• {factor}")
        
        # Gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico de pizza - distribuição de despesas
            expense_chart = analytics.create_expense_distribution_chart(current_year, current_month)
            if expense_chart:
                st.plotly_chart(expense_chart, use_container_width=True)
        
        with col2:
            # Gráfico de tendência mensal
            trend_chart = analytics.create_monthly_trend_chart()
            if trend_chart:
                st.plotly_chart(trend_chart, use_container_width=True)
        
        # Alertas de anomalias
        anomalies = analytics.detect_anomalies()
        if anomalies:
            st.subheader("⚠️ Alertas de Gastos Anômalos")
            for anomaly in anomalies[:3]:  # Mostrar apenas os 3 principais
                severity_color = "danger-card" if anomaly['severity'] == 'alta' else "warning-card"
                st.markdown(f"""
                <div class="metric-card {severity_color}">
                    <strong>{anomaly['description']}</strong><br>
                    Categoria: {anomaly['category']} | Valor: R$ {anomaly['amount']:,.2f}<br>
                    Data: {anomaly['date']} | Severidade: {anomaly['severity']}
                </div>
                """, unsafe_allow_html=True)
                st.write("")
    
    else:
        st.info("📝 Adicione algumas transações para ver o dashboard completo!")

def show_add_transaction(db):
    st.header("➕ Adicionar Nova Transação")
    
    with st.form("transaction_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            transaction_date = st.date_input(
                "📅 Data da Transação",
                value=date.today(),
                max_value=date.today()
            )
            
            transaction_type = st.selectbox(
                "💱 Tipo de Transação",
                ["despesa", "receita"]
            )
            
            # Buscar categorias do tipo selecionado
            categories_df = db.get_categories(transaction_type)
            categories = categories_df['name'].tolist() if not categories_df.empty else []
            
            category = st.selectbox(
                "🏷️ Categoria",
                categories
            )
            
            due_date = st.date_input(
                "📅 Data de Vencimento",
                value=None,
                help="Deixe vazio se já foi pago"
            )
        
        with col2:
            description = st.text_input(
                "📝 Descrição",
                placeholder="Ex: Almoço no restaurante"
            )
            
            amount = st.number_input(
                "💰 Valor (R$)",
                min_value=0.01,
                step=0.01,
                format="%.2f"
            )
            
            status = st.selectbox(
                "📊 Status",
                ["pendente", "pago", "cancelado"]
            )
        
        submitted = st.form_submit_button("💾 Salvar Transação", use_container_width=True)
        
        if submitted:
            if description and amount > 0:
                try:
                    due_date_str = due_date.strftime('%Y-%m-%d') if due_date else None
                    db.add_transaction(
                        description=description,
                        amount=amount,
                        transaction_type=transaction_type,
                        category=category,
                        date=transaction_date.strftime('%Y-%m-%d'),
                        due_date=due_date_str,
                        status=status
                    )
                    st.success("✅ Transação adicionada com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro ao salvar transação: {str(e)}")
            else:
                st.error("❌ Por favor, preencha todos os campos obrigatórios!")

def show_history(db):
    st.header("📋 Histórico de Transações")
    
    # Criar abas para organizar funcionalidades
    tab1, tab2, tab3 = st.tabs(["📊 Visualizar", "✏️ Editar", "🔍 Buscar"])
    
    with tab1:
        # Filtros
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            start_date = st.date_input(
                "📅 Data Inicial",
                value=date.today() - timedelta(days=30)
            )
        
        with col2:
            end_date = st.date_input(
                "📅 Data Final",
                value=date.today()
            )
        
        with col3:
            transaction_type_filter = st.selectbox(
                "💱 Filtrar por Tipo",
                ["Todos", "receita", "despesa"]
            )
        
        with col4:
            status_filter = st.selectbox(
                "📊 Filtrar por Status",
                ["Todos", "pendente", "pago", "cancelado"]
            )
        
        # Buscar transações
        df = db.get_transactions(start_date, end_date)
        
        if not df.empty:
            # Aplicar filtro de tipo se selecionado
            if transaction_type_filter != "Todos":
                df = df[df['type'] == transaction_type_filter]
            
            # Aplicar filtro de status se selecionado
            if status_filter != "Todos":
                df = df[df['status'] == status_filter]
            
            # Formatação dos dados
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%d/%m/%Y')
            df['due_date_formatted'] = df['due_date'].apply(lambda x: pd.to_datetime(x).strftime('%d/%m/%Y') if pd.notna(x) else '-')
            df['amount_formatted'] = df['amount'].apply(lambda x: f"R$ {x:,.2f}")
            df['status_formatted'] = df['status'].apply(lambda x: {
                'pendente': '⏳ Pendente',
                'pago': '✅ Pago',
                'cancelado': '❌ Cancelado'
            }.get(x, '⏳ Pendente'))
            
            # Destacar transações em atraso
            if 'status' in df.columns and 'due_date' in df.columns:
                try:
                    today = pd.Timestamp.now()
                    df['due_date_parsed'] = pd.to_datetime(df['due_date'], errors='coerce')
                    df['is_overdue'] = (
                        (df['status'] == 'pendente') & 
                        (pd.notna(df['due_date_parsed'])) & 
                        (df['due_date_parsed'] < today)
                    )
                except:
                    df['is_overdue'] = False
            else:
                df['is_overdue'] = False
            
            # Exibir tabela
            display_df = df[['date', 'description', 'category', 'amount_formatted', 'type', 'due_date_formatted', 'status_formatted']].rename(columns={
                'date': 'Data',
                'description': 'Descrição',
                'category': 'Categoria',
                'amount_formatted': 'Valor',
                'type': 'Tipo',
                'due_date_formatted': 'Vencimento',
                'status_formatted': 'Status'
            })
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
            
            # Mostrar transações em atraso
            overdue_transactions = df[df['is_overdue']]
            if not overdue_transactions.empty:
                st.warning(f"⚠️ {len(overdue_transactions)} transação(ões) em atraso!")
            
            # Estatísticas do período
            if not df.empty:
                st.subheader("📊 Estatísticas do Período")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    total_receitas = df[df['type'] == 'receita']['amount'].sum()
                    st.metric("💰 Total Receitas", f"R$ {total_receitas:,.2f}")
                
                with col2:
                    total_despesas = df[df['type'] == 'despesa']['amount'].sum()
                    st.metric("💸 Total Despesas", f"R$ {total_despesas:,.2f}")
                
                with col3:
                    saldo = total_receitas - total_despesas
                    st.metric("📈 Saldo", f"R$ {saldo:,.2f}")
                
                with col4:
                    total_transacoes = len(df)
                    st.metric("📋 Total Transações", total_transacoes)
        else:
            st.info("📭 Nenhuma transação encontrada no período selecionado.")
    
    with tab2:
        st.subheader("✏️ Editar Transações")
        
        # Buscar todas as transações para edição
        all_df = db.get_transactions(date.today() - timedelta(days=365), date.today() + timedelta(days=365))
        
        if not all_df.empty:
            # Seletor de transação para editar
            transaction_options = [(row['id'], f"{row['description']} - R$ {row['amount']:,.2f} ({pd.to_datetime(row['date']).strftime('%d/%m/%Y')})") for _, row in all_df.iterrows()]
            
            selected_transaction_id = st.selectbox(
                "🔍 Selecionar Transação para Editar",
                options=[opt[0] for opt in transaction_options],
                format_func=lambda x: next(opt[1] for opt in transaction_options if opt[0] == x)
            )
            
            if selected_transaction_id:
                # Buscar dados da transação selecionada
                transaction_data = db.get_transaction_by_id(selected_transaction_id)
                
                if transaction_data:
                    st.divider()
                    st.subheader("📝 Formulário de Edição")
                    
                    # Mapear os dados da transação baseado na estrutura da tabela
                    # (id, date, description, amount, category, type, created_at, due_date, status)
                    transaction_id = transaction_data[0]
                    transaction_date = transaction_data[1]
                    transaction_description = transaction_data[2]
                    transaction_amount = transaction_data[3]
                    transaction_category = transaction_data[4]
                    transaction_type = transaction_data[5]
                    transaction_created_at = transaction_data[6]
                    transaction_due_date = transaction_data[7] if len(transaction_data) > 7 else None
                    transaction_status = transaction_data[8] if len(transaction_data) > 8 else 'pendente'
                    
                    # Formulário de edição
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        new_description = st.text_input(
                            "📝 Descrição",
                            value=transaction_description
                        )
                        
                        new_amount = st.number_input(
                            "💰 Valor",
                            value=float(transaction_amount),
                            min_value=0.01,
                            step=0.01,
                            format="%.2f"
                        )
                        
                        # Buscar categorias disponíveis
                        categories_df = db.get_categories()
                        category_options = categories_df['name'].tolist() if not categories_df.empty else []
                        
                        current_category_index = 0
                        if transaction_category in category_options:
                            current_category_index = category_options.index(transaction_category)
                        
                        new_category = st.selectbox(
                            "🏷️ Categoria",
                            options=category_options,
                            index=current_category_index
                        )
                    
                    with col2:
                        new_type = st.selectbox(
                            "💱 Tipo",
                            options=["receita", "despesa"],
                            index=0 if transaction_type == "receita" else 1
                        )
                        
                        new_date = st.date_input(
                            "📅 Data",
                            value=pd.to_datetime(transaction_date).date()
                        )
                        
                        # Due date (pode ser None)
                        current_due_date = None
                        if transaction_due_date:
                            try:
                                current_due_date = pd.to_datetime(transaction_due_date).date()
                            except:
                                current_due_date = None
                        
                        new_due_date = st.date_input(
                            "📅 Data de Vencimento (opcional)",
                            value=current_due_date
                        )
                        
                        status_options = ["pendente", "pago", "cancelado"]
                        current_status_index = 0
                        if transaction_status in status_options:
                            current_status_index = status_options.index(transaction_status)
                        
                        new_status = st.selectbox(
                            "📊 Status",
                            options=status_options,
                            index=current_status_index
                        )
                    
                    # Botões de ação
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("💾 Salvar Alterações", type="primary"):
                            try:
                                db.update_transaction(
                                    selected_transaction_id,
                                    new_description,
                                    new_amount,
                                    new_category,
                                    new_type,
                                    new_date,
                                    new_due_date if new_due_date else None,
                                    new_status
                                )
                                st.success("✅ Transação atualizada com sucesso!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erro ao atualizar transação: {str(e)}")
                    
                    with col2:
                        if st.button("🗑️ Excluir Transação", type="secondary"):
                            try:
                                db.delete_transaction(selected_transaction_id)
                                st.success("✅ Transação excluída com sucesso!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erro ao excluir transação: {str(e)}")
                    
                    with col3:
                        if st.button("🔄 Atualizar Apenas Status"):
                            try:
                                db.update_transaction_status(selected_transaction_id, new_status)
                                st.success("✅ Status atualizado!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Erro ao atualizar status: {str(e)}")
        else:
            st.info("📭 Nenhuma transação encontrada para edição.")
    
    with tab3:
        st.subheader("🔍 Busca Avançada")
        
        # Filtros de busca
        col1, col2 = st.columns(2)
        
        with col1:
            search_description = st.text_input("🔍 Buscar por descrição")
            search_category = st.text_input("🏷️ Buscar por categoria")
        
        with col2:
            search_amount_min = st.number_input("💰 Valor mínimo", min_value=0.0, step=0.01)
            search_amount_max = st.number_input("💰 Valor máximo", min_value=0.0, step=0.01)
        
        if st.button("🔍 Buscar"):
            # Buscar todas as transações
            search_df = db.get_transactions(date.today() - timedelta(days=365*2), date.today() + timedelta(days=365))
            
            if not search_df.empty:
                # Aplicar filtros de busca
                if search_description:
                    search_df = search_df[search_df['description'].str.contains(search_description, case=False, na=False)]
                
                if search_category:
                    search_df = search_df[search_df['category'].str.contains(search_category, case=False, na=False)]
                
                if search_amount_min > 0:
                    search_df = search_df[search_df['amount'] >= search_amount_min]
                
                if search_amount_max > 0:
                    search_df = search_df[search_df['amount'] <= search_amount_max]
                
                if not search_df.empty:
                    # Formatação dos resultados
                    search_df['date'] = pd.to_datetime(search_df['date']).dt.strftime('%d/%m/%Y')
                    search_df['amount_formatted'] = search_df['amount'].apply(lambda x: f"R$ {x:,.2f}")
                    
                    display_search_df = search_df[['date', 'description', 'category', 'amount_formatted', 'type', 'status']].rename(columns={
                        'date': 'Data',
                        'description': 'Descrição',
                        'category': 'Categoria',
                        'amount_formatted': 'Valor',
                        'type': 'Tipo',
                        'status': 'Status'
                    })
                    
                    st.dataframe(
                        display_search_df,
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    st.info(f"📊 {len(search_df)} transação(ões) encontrada(s)")
                else:
                    st.warning("🔍 Nenhuma transação encontrada com os critérios especificados.")
            else:
                st.info("📭 Nenhuma transação disponível para busca.")

def show_analytics(db, analytics):
    st.header("📊 Análises Detalhadas")
    
    # Análise mensal
    st.subheader("📅 Análise Mensal")
    
    col1, col2 = st.columns(2)
    
    with col1:
        analysis_year = st.selectbox("Ano", range(2020, 2030), index=4)  # 2024 como padrão
    
    with col2:
        analysis_month = st.selectbox("Mês", range(1, 13), index=datetime.now().month - 1)
    
    insights = analytics.calculate_category_insights(analysis_year, analysis_month)
    
    if insights:
        # Métricas do mês selecionado
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("💰 Receitas", f"R$ {insights['total_income']:,.2f}")
        
        with col2:
            st.metric("💸 Despesas", f"R$ {insights['total_expenses']:,.2f}")
        
        with col3:
            st.metric("📊 Taxa de Poupança", f"{insights['savings_rate']:.1f}%")
        
        # Top categorias de despesa
        if insights['top_expense_categories']:
            st.subheader("🏆 Top 5 Categorias de Despesa")
            
            top_categories = pd.DataFrame(insights['top_expense_categories'])
            
            fig = px.bar(
                top_categories,
                x='category',
                y='total',
                title=f"Maiores Despesas - {analysis_month:02d}/{analysis_year}",
                labels={'category': 'Categoria', 'total': 'Valor (R$)'}
            )
            
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    # Detecção de anomalias
    st.subheader("🔍 Detecção de Anomalias")
    
    anomalies = analytics.detect_anomalies()
    
    if anomalies:
        st.write(f"Encontradas **{len(anomalies)}** transações anômalas:")
        
        anomalies_df = pd.DataFrame(anomalies)
        anomalies_df['date'] = pd.to_datetime(anomalies_df['date']).dt.strftime('%d/%m/%Y')
        anomalies_df['amount_formatted'] = anomalies_df['amount'].apply(lambda x: f"R$ {x:,.2f}")
        
        st.dataframe(
            anomalies_df[['date', 'description', 'category', 'amount_formatted', 'severity']].rename(columns={
                'date': 'Data',
                'description': 'Descrição',
                'category': 'Categoria',
                'amount_formatted': 'Valor',
                'severity': 'Severidade'
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("✅ Nenhuma anomalia detectada nos últimos 6 meses.")

def show_projections(db, analytics):
    st.header("🔮 Projeções Anuais")
    
    projections = analytics.predict_annual_projection()
    
    if projections:
        st.subheader("📈 Projeção por Categoria")
        
        # Gráfico de projeção
        projection_chart = analytics.create_projection_chart()
        if projection_chart:
            st.plotly_chart(projection_chart, use_container_width=True)
        
        # Tabela detalhada
        st.subheader("📋 Detalhes das Projeções")
        
        projection_data = []
        for category, data in projections.items():
            projection_data.append({
                'Categoria': category,
                'Projeção Anual': f"R$ {data['annual_total']:,.2f}",
                'Média Mensal': f"R$ {data['average_monthly']:,.2f}",
                'Tendência': data['trend'],
                'Confiança': f"{data['confidence']*100:.0f}%"
            })
        
        projection_df = pd.DataFrame(projection_data)
        st.dataframe(projection_df, use_container_width=True, hide_index=True)
        
        # Resumo total
        total_projected = sum([data['annual_total'] for data in projections.values()])
        st.metric("💰 Projeção Total Anual", f"R$ {total_projected:,.2f}")
        
        st.info("💡 **Dica:** As projeções são baseadas em dados históricos e podem variar conforme mudanças nos seus hábitos financeiros.")
    
    else:
        st.warning("📊 Dados insuficientes para gerar projeções. Adicione mais transações para obter análises preditivas.")

def show_settings(db):
    st.header("⚙️ Configurações")
    
    # Tabs para organizar melhor
    tab1, tab2, tab3 = st.tabs(["🏷️ Gerenciar Categorias", "➕ Adicionar Categoria", "📤 Exportar Dados"])
    
    with tab1:
        st.subheader("📋 Categorias Existentes")
        
        # Mostrar categorias existentes
        categories_df = db.get_categories()
        
        if not categories_df.empty:
            # Separar por tipo
            despesas_df = categories_df[categories_df['type'] == 'despesa']
            receitas_df = categories_df[categories_df['type'] == 'receita']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**💸 Categorias de Despesa:**")
                if not despesas_df.empty:
                    for _, category in despesas_df.iterrows():
                        with st.expander(f"🏷️ {category['name']} - R$ {category['budget']:.2f}"):
                            edit_category_form(db, category)
                else:
                    st.info("Nenhuma categoria de despesa encontrada.")
            
            with col2:
                st.write("**💰 Categorias de Receita:**")
                if not receitas_df.empty:
                    for _, category in receitas_df.iterrows():
                        with st.expander(f"🏷️ {category['name']} - R$ {category['budget']:.2f}"):
                            edit_category_form(db, category)
                else:
                    st.info("Nenhuma categoria de receita encontrada.")
        else:
            st.warning("⚠️ Nenhuma categoria encontrada.")
    
    with tab2:
        st.subheader("➕ Adicionar Nova Categoria")
        
        with st.form("add_category_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_category_name = st.text_input("Nome da Categoria")
                new_category_type = st.selectbox("Tipo", ["despesa", "receita"])
            
            with col2:
                new_category_budget = st.number_input("Orçamento Mensal (R$)", min_value=0.0, step=10.0)
                new_category_color = st.color_picker("Cor da Categoria", "#95a5a6")
            
            if st.form_submit_button("➕ Adicionar Categoria", use_container_width=True):
                if new_category_name:
                    try:
                        db.add_category(new_category_name, new_category_type, new_category_budget, new_category_color)
                        st.success(f"✅ Categoria '{new_category_name}' adicionada com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao adicionar categoria: {str(e)}")
                else:
                    st.error("❌ Por favor, insira o nome da categoria.")
    
    with tab3:
        st.subheader("📤 Exportar Dados")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Exportar para Excel", use_container_width=True):
                # Aqui você adicionaria a lógica de exportação
                st.info("🔄 Funcionalidade de exportação em desenvolvimento...")
        
        with col2:
            if st.button("📄 Gerar Relatório PDF", use_container_width=True):
                # Aqui você adicionaria a lógica de geração de PDF
                st.info("🔄 Funcionalidade de relatório em desenvolvimento...")

def edit_category_form(db, category):
    """Formulário para editar uma categoria específica"""
    col1, col2 = st.columns(2)
    
    with col1:
        new_name = st.text_input("Nome:", value=category['name'], key=f"name_{category['id']}")
        new_budget = st.number_input("Orçamento (R$):", value=float(category['budget']), min_value=0.0, step=10.0, key=f"budget_{category['id']}")
    
    with col2:
        new_color = st.color_picker("Cor:", value=category['color'], key=f"color_{category['id']}")
        st.write(f"**Tipo:** {category['type'].title()}")
    
    col_update, col_delete = st.columns(2)
    
    with col_update:
        if st.button("💾 Atualizar", key=f"update_{category['id']}", use_container_width=True):
            try:
                db.update_category(category['id'], name=new_name, budget=new_budget, color=new_color)
                st.success("✅ Categoria atualizada!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erro ao atualizar: {str(e)}")
    
    with col_delete:
        if st.button("🗑️ Excluir", key=f"delete_{category['id']}", use_container_width=True, type="secondary"):
            success, message = db.delete_category(category['id'])
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

if __name__ == "__main__":
    main()