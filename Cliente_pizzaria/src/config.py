import os

# ==============================================================================
# CONFIGURAÇÃO - PIZZARIA IMPULSA (CORREÇÃO DE DATA)
# ==============================================================================

# --- IDENTIDADE ---
NOME_CLIENTE = "Pizzaria Impulsa"
MOEDA = "R$"

# --- CAMINHOS ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_DIR = os.path.join(BASE_DIR, 'dados', 'input')
ARQUIVO_PROCESSADO = os.path.join(INPUT_DIR, 'pizzaria_sales_processed.csv')

# --- DEFINIÇÃO DO SCHEMA ---
COLUNAS_OFICIAIS = [
    'order_id', 'order_date', 'order_time', 'order_datetime',
    'day_of_week', 'hour_of_day', 'month_name',
    'pizza_name', 'pizza_category', 'pizza_size', 'pizza_price',
    'quantity', 'total_item_value'
]

# --- TIPAGEM ---
# Colunas de Data
COLUNAS_DATA = ['order_date', 'order_datetime']

# Colunas Numéricas
COLUNAS_NUMERICAS = {
    'order_id': 'int64',
    'hour_of_day': 'int64',
    'quantity': 'int64',
    'pizza_price': 'float64',
    'total_item_value': 'float64'
}