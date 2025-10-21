  
  
  
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

class FinanceAnalytics:
    def __init__(self, database):
        self.db = database
    
    def get_monthly_trends(self, months=12):
        """Analisa tendências mensais dos últimos N meses"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months*30)
        
        df = self.db.get_transactions(start_date.date(), end_date.date())
        
        if df.empty:
            return pd.DataFrame()
        
        df['date'] = pd.to_datetime(df['date'])
        df['year_month'] = df['date'].dt.to_period('M')
        
        # Agrupa por mês e tipo
        monthly_summary = df.groupby(['year_month', 'type'])['amount'].sum().reset_index()
        monthly_summary['year_month_str'] = monthly_summary['year_month'].astype(str)
        
        return monthly_summary
    
    def calculate_category_insights(self, year, month):
        """Calcula insights por categoria para um mês específico"""
        monthly_data = self.db.get_monthly_summary(year, month)
        
        if monthly_data.empty:
            return {}
        
        # Separar receitas e despesas
        expenses = monthly_data[monthly_data['type'] == 'despesa']
        income = monthly_data[monthly_data['type'] == 'receita']
        
        total_expenses = expenses['total'].sum()
        total_income = income['total'].sum()
        
        insights = {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'balance': total_income - total_expenses,
            'savings_rate': ((total_income - total_expenses) / total_income * 100) if total_income > 0 else 0,
            'top_expense_categories': expenses.nlargest(5, 'total').to_dict('records'),
            'expense_distribution': expenses.set_index('category')['total'].to_dict()
        }
        
        return insights
    
    def predict_annual_projection(self):
        """Cria projeção anual baseada em dados históricos"""
        # Pega dados dos últimos 12 meses
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        df = self.db.get_transactions(start_date.date(), end_date.date())
        
        if df.empty or len(df) < 3:
            return None
        
        df['date'] = pd.to_datetime(df['date'])
        df['month_num'] = df['date'].dt.month
        
        # Agrupa por mês e categoria
        monthly_category = df.groupby(['month_num', 'category', 'type'])['amount'].sum().reset_index()
        
        projections = {}
        
        for category in monthly_category['category'].unique():
            cat_data = monthly_category[monthly_category['category'] == category]
            
            if len(cat_data) >= 3:  # Precisa de pelo menos 3 pontos para projeção
                X = cat_data['month_num'].values.reshape(-1, 1)
                y = cat_data['amount'].values
                
                # Regressão linear simples
                model = LinearRegression()
                model.fit(X, y)
                
                # Projeção para os próximos 12 meses
                future_months = np.arange(1, 13).reshape(-1, 1)
                predictions = model.predict(future_months)
                
                # Garantir que não há valores negativos para despesas
                predictions = np.maximum(predictions, 0)
                
                projections[category] = {
                    'monthly_predictions': predictions.tolist(),
                    'annual_total': float(predictions.sum()),
                    'average_monthly': float(predictions.mean()),
                    'trend': 'crescente' if model.coef_[0] > 0 else 'decrescente',
                    'confidence': min(len(cat_data) / 12, 1.0)  # Confiança baseada em dados disponíveis
                }
        
        return projections
    
    def detect_anomalies(self, threshold=2):
        """Detecta gastos anômalos usando desvio padrão"""
        # Pega dados dos últimos 6 meses
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        
        df = self.db.get_transactions(start_date.date(), end_date.date())
        
        if df.empty:
            return []
        
        anomalies = []
        
        for category in df['category'].unique():
            cat_data = df[df['category'] == category]
            
            if len(cat_data) < 5:  # Precisa de dados suficientes
                continue
            
            mean_amount = cat_data['amount'].mean()
            std_amount = cat_data['amount'].std()
            
            # Detecta valores que estão além do threshold de desvios padrão
            for _, transaction in cat_data.iterrows():
                z_score = abs((transaction['amount'] - mean_amount) / std_amount) if std_amount > 0 else 0
                
                if z_score > threshold:
                    anomalies.append({
                        'id': transaction['id'],
                        'date': transaction['date'],
                        'description': transaction['description'],
                        'amount': transaction['amount'],
                        'category': transaction['category'],
                        'z_score': z_score,
                        'severity': 'alta' if z_score > 3 else 'média'
                    })
        
        return sorted(anomalies, key=lambda x: x['z_score'], reverse=True)
    
    def create_expense_distribution_chart(self, year, month):
        """Cria gráfico de distribuição de despesas"""
        monthly_data = self.db.get_monthly_summary(year, month)
        expenses = monthly_data[monthly_data['type'] == 'despesa']
        
        if expenses.empty:
            return None
        
        fig = px.pie(
            expenses, 
            values='total', 
            names='category',
            title=f'Distribuição de Despesas - {month:02d}/{year}',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(showlegend=True, height=500)
        
        return fig
    
    def create_monthly_trend_chart(self):
        """Cria gráfico de tendência mensal"""
        trends = self.get_monthly_trends(12)
        
        if trends.empty:
            return None
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Receitas
        income_data = trends[trends['type'] == 'receita']
        if not income_data.empty:
            fig.add_trace(
                go.Scatter(
                    x=income_data['year_month_str'],
                    y=income_data['amount'],
                    mode='lines+markers',
                    name='Receitas',
                    line=dict(color='green', width=3)
                )
            )
        
        # Despesas
        expense_data = trends[trends['type'] == 'despesa']
        if not expense_data.empty:
            fig.add_trace(
                go.Scatter(
                    x=expense_data['year_month_str'],
                    y=expense_data['amount'],
                    mode='lines+markers',
                    name='Despesas',
                    line=dict(color='red', width=3)
                )
            )
        
        fig.update_layout(
            title='Tendência Mensal - Receitas vs Despesas',
            xaxis_title='Mês',
            yaxis_title='Valor (R$)',
            height=500,
            hovermode='x unified'
        )
        
        return fig
    
    def create_projection_chart(self):
        """Cria gráfico de projeção anual"""
        projections = self.predict_annual_projection()
        
        if not projections:
            return None
        
        categories = list(projections.keys())
        annual_totals = [projections[cat]['annual_total'] for cat in categories]
        
        fig = go.Figure(data=[
            go.Bar(
                x=categories,
                y=annual_totals,
                text=[f'R$ {val:,.0f}' for val in annual_totals],
                textposition='auto',
                marker_color='lightblue'
            )
        ])
        
        fig.update_layout(
            title='Projeção Anual por Categoria',
            xaxis_title='Categoria',
            yaxis_title='Valor Projetado (R$)',
            height=500,
            xaxis_tickangle=-45
        )
        
        return fig
    
    def generate_financial_score(self):
        """Gera um score financeiro baseado em múltiplos fatores"""
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        insights = self.calculate_category_insights(current_year, current_month)
        
        if not insights:
            return 0, "Dados insuficientes"
        
        score = 0
        factors = []
        
        # Fator 1: Taxa de poupança (0-40 pontos)
        savings_rate = insights['savings_rate']
        if savings_rate >= 20:
            score += 40
            factors.append("Excelente taxa de poupança")
        elif savings_rate >= 10:
            score += 30
            factors.append("Boa taxa de poupança")
        elif savings_rate >= 0:
            score += 20
            factors.append("Taxa de poupança baixa")
        else:
            score += 0
            factors.append("Gastando mais que ganha")
        
        # Fator 2: Diversificação de gastos (0-30 pontos)
        expense_categories = len(insights['expense_distribution'])
        if expense_categories >= 5:
            score += 30
            factors.append("Boa diversificação de gastos")
        elif expense_categories >= 3:
            score += 20
            factors.append("Diversificação moderada")
        else:
            score += 10
            factors.append("Poucos tipos de gastos registrados")
        
        # Fator 3: Consistência (0-30 pontos)
        # Baseado na quantidade de transações
        monthly_data = self.db.get_monthly_summary(current_year, current_month)
        total_transactions = monthly_data['count'].sum() if not monthly_data.empty else 0
        
        if total_transactions >= 20:
            score += 30
            factors.append("Registro consistente de transações")
        elif total_transactions >= 10:
            score += 20
            factors.append("Registro moderado de transações")
        else:
            score += 10
            factors.append("Poucos registros de transações")
        
        return min(score, 100), factors