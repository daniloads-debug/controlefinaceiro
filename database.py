import sqlite3
import pandas as pd
from datetime import datetime, date
import os

class FinanceDatabase:
    def __init__(self, db_path="finance_data.db"):
        self.db_path = db_path
        self.init_database()
        self.migrate_database()
    
    def init_database(self):
        """Inicializa o banco de dados com as tabelas necessárias"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de transações
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                type TEXT NOT NULL CHECK (type IN ('receita', 'despesa')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                due_date TEXT,
                status TEXT DEFAULT 'pendente'
            )
        ''')
        
        # Tabela de categorias
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL CHECK (type IN ('receita', 'despesa')),
                budget REAL DEFAULT 0,
                color TEXT DEFAULT '#3498db'
            )
        ''')
        
        # Tabela de metas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                monthly_budget REAL NOT NULL,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Inserir categorias padrão se não existirem
        self.insert_default_categories()
    
    def insert_default_categories(self):
        """Insere categorias padrão no banco baseadas em melhores práticas financeiras"""
        default_categories = [
            # DESPESAS ESSENCIAIS (50-60% da renda)
            ('Moradia', 'despesa', 1500, '#8B4513'),  # Aluguel, financiamento, condomínio
            ('Alimentação - Casa', 'despesa', 600, '#FF6347'),  # Supermercado, feira
            ('Transporte', 'despesa', 400, '#FF8C00'),  # Combustível, transporte público
            ('Saúde', 'despesa', 300, '#32CD32'),  # Plano de saúde, medicamentos
            ('Seguros', 'despesa', 200, '#4682B4'),  # Seguro auto, vida, residencial
            ('Impostos e Taxas', 'despesa', 150, '#696969'),  # IPTU, IPVA, taxas
            
            # DESPESAS VARIÁVEIS (20-30% da renda)
            ('Alimentação - Fora', 'despesa', 300, '#FF4500'),  # Restaurantes, delivery
            ('Lazer e Entretenimento', 'despesa', 250, '#9370DB'),  # Cinema, shows, viagens
            ('Vestuário', 'despesa', 200, '#DA70D6'),  # Roupas, calçados, acessórios
            ('Educação', 'despesa', 300, '#20B2AA'),  # Cursos, livros, capacitação
            ('Cuidados Pessoais', 'despesa', 150, '#FFB6C1'),  # Salão, produtos de higiene
            ('Casa e Decoração', 'despesa', 100, '#DEB887'),  # Móveis, utensílios, reparos
            ('Tecnologia', 'despesa', 100, '#4169E1'),  # Internet, celular, streaming
            ('Pets', 'despesa', 80, '#F0E68C'),  # Ração, veterinário, produtos
            
            # DESPESAS EVENTUAIS
            ('Presentes e Doações', 'despesa', 100, '#FF69B4'),  # Aniversários, caridade
            ('Emergências', 'despesa', 200, '#DC143C'),  # Imprevistos, reparos urgentes
            ('Outros Gastos', 'despesa', 50, '#A9A9A9'),  # Diversos não categorizados
            
            # RECEITAS
            ('Salário CLT', 'receita', 0, '#228B22'),  # Salário principal
            ('Renda Extra', 'receita', 0, '#32CD32'),  # Freelances, trabalhos extras
            ('Investimentos', 'receita', 0, '#006400'),  # Dividendos, juros, rendimentos
            ('Vendas', 'receita', 0, '#7CFC00'),  # Vendas de produtos/serviços
            ('Restituição/Benefícios', 'receita', 0, '#ADFF2F'),  # IR, auxílios, benefícios
            ('Outras Receitas', 'receita', 0, '#9ACD32')  # Receitas diversas
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for name, type_cat, budget, color in default_categories:
            cursor.execute('''
                INSERT OR IGNORE INTO categories (name, type, budget, color)
                VALUES (?, ?, ?, ?)
            ''', (name, type_cat, budget, color))
        
        conn.commit()
        conn.close()
    
    def migrate_database(self):
        """Migra o banco de dados para adicionar novas colunas se necessário"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verificar se as colunas existem
        cursor.execute("PRAGMA table_info(transactions)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Adicionar coluna due_date se não existir
        if 'due_date' not in columns:
            cursor.execute('ALTER TABLE transactions ADD COLUMN due_date TEXT')
            
        # Adicionar coluna status se não existir
        if 'status' not in columns:
            cursor.execute('ALTER TABLE transactions ADD COLUMN status TEXT DEFAULT "pendente"')
            
        conn.commit()
        conn.close()
    
    def add_transaction(self, description, amount, transaction_type, category, date=None, due_date=None, status='pendente'):
        """Adiciona uma nova transação"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO transactions (description, amount, type, category, date, due_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (description, amount, transaction_type, category, date, due_date, status))
        
        conn.commit()
        conn.close()
        return cursor.lastrowid
    
    def get_transactions(self, start_date=None, end_date=None):
        """Recupera transações com filtros opcionais"""
        conn = sqlite3.connect(self.db_path)
        
        query = "SELECT * FROM transactions"
        params = []
        
        if start_date and end_date:
            query += " WHERE date BETWEEN ? AND ?"
            params = [start_date, end_date]
        elif start_date:
            query += " WHERE date >= ?"
            params = [start_date]
        elif end_date:
            query += " WHERE date <= ?"
            params = [end_date]
        
        query += " ORDER BY date DESC"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        return df
    
    def get_categories(self, transaction_type=None):
        """Recupera categorias"""
        conn = sqlite3.connect(self.db_path)
        
        if transaction_type:
            df = pd.read_sql_query(
                "SELECT * FROM categories WHERE type = ? ORDER BY name",
                conn, params=[transaction_type]
            )
        else:
            df = pd.read_sql_query("SELECT * FROM categories ORDER BY name", conn)
        
        conn.close()
        return df
    
    def get_monthly_summary(self, year, month):
        """Gera resumo mensal"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT 
                category,
                type,
                SUM(amount) as total,
                COUNT(*) as count
            FROM transactions 
            WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
            GROUP BY category, type
            ORDER BY total DESC
        '''
        
        df = pd.read_sql_query(query, conn, params=[str(year), f"{month:02d}"])
        conn.close()
        
        return df
    
    def delete_transaction(self, transaction_id):
        """Remove uma transação"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        
        conn.commit()
        conn.close()
    
    def update_transaction_status(self, transaction_id, status):
        """Atualiza o status de uma transação"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE transactions SET status = ? WHERE id = ?
        ''', (status, transaction_id))
        conn.commit()
        conn.close()
    
    def update_transaction(self, transaction_id, description, amount, category, transaction_type, date, due_date=None, status='pendente'):
        """Atualiza uma transação completa"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Converter date para string se necessário
        if isinstance(date, (datetime, datetime.date)):
            date = date.strftime('%Y-%m-%d')
        
        # Converter due_date para string se necessário
        if due_date and isinstance(due_date, (datetime, datetime.date)):
            due_date = due_date.strftime('%Y-%m-%d')
        
        cursor.execute('''
            UPDATE transactions 
            SET description = ?, amount = ?, category = ?, type = ?, date = ?, due_date = ?, status = ?
            WHERE id = ?
        ''', (description, amount, category, transaction_type, date, due_date, status, transaction_id))
        
        conn.commit()
        conn.close()
        return True
    
    def get_transaction_by_id(self, transaction_id):
        """Recupera uma transação específica pelo ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,))
        transaction = cursor.fetchone()
        
        conn.close()
        return transaction
    
    def get_pending_transactions(self):
        """Retorna transações pendentes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM transactions WHERE status = 'pendente' ORDER BY due_date, date
        ''')
        transactions = cursor.fetchall()
        conn.close()
        return transactions
    
    def add_category(self, name, category_type, budget=0, color='#95a5a6'):
        """Adiciona uma nova categoria"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO categories (name, type, budget, color)
            VALUES (?, ?, ?, ?)
        ''', (name, category_type, budget, color))
        
        conn.commit()
        conn.close()
        return cursor.lastrowid
    
    def update_category(self, category_id, name=None, budget=None, color=None):
        """Atualiza uma categoria existente"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Construir query dinamicamente baseado nos parâmetros fornecidos
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        
        if budget is not None:
            updates.append("budget = ?")
            params.append(budget)
        
        if color is not None:
            updates.append("color = ?")
            params.append(color)
        
        if updates:
            query = f"UPDATE categories SET {', '.join(updates)} WHERE id = ?"
            params.append(category_id)
            cursor.execute(query, params)
        
        conn.commit()
        conn.close()
    
    def delete_category(self, category_id):
        """Remove uma categoria (apenas se não houver transações vinculadas)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verificar se existem transações vinculadas a esta categoria
        cursor.execute("SELECT COUNT(*) FROM transactions WHERE category = (SELECT name FROM categories WHERE id = ?)", (category_id,))
        count = cursor.fetchone()[0]
        
        if count > 0:
            conn.close()
            return False, f"Não é possível excluir a categoria. Existem {count} transação(ões) vinculada(s) a ela."
        
        # Se não houver transações, pode deletar
        cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        
        conn.commit()
        conn.close()
        return True, "Categoria excluída com sucesso!"
    
    def get_category_by_id(self, category_id):
        """Recupera uma categoria específica pelo ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
        category = cursor.fetchone()
        
        conn.close()
        return category
    
    def get_overdue_transactions(self):
        """Retorna transações em atraso"""
        today = datetime.now().strftime('%Y-%m-%d')
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM transactions 
            WHERE status = 'pendente' AND due_date < ? AND due_date IS NOT NULL
            ORDER BY due_date
        ''', (today,))
        transactions = cursor.fetchall()
        conn.close()
        return transactions