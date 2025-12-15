import os

# ==============================================================================
# CONFIGURAÇÃO - IMOBILIÁRIA IMPULSA (V 3.0)
# ==============================================================================

# --- IDENTIDADE ---
NOME_CLIENTE = "Imobiliária Impulsa"
MOEDA = "R$"

# --- CAMINHOS ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_DIR = os.path.join(BASE_DIR, 'dados', 'input')
ARQUIVO_PROCESSADO = os.path.join(INPUT_DIR, 'imoveis_processados.csv')

# --- DEFINIÇÃO DO SCHEMA ---
COLUNAS_OFICIAIS = [
    'ID', 
    'Cidade', 
    'Area', 
    'Quartos', 
    'Banheiros', 
    'Vagas garagem', 
    'Aceita Animais', 
    'Mobilhado', 
    'Valor condomínio', 
    'Valor do Aluguel', 
    'IPTU', 
    'Seguro',
    'Tipo Imóvel',
    'Bairro',
    'Estado'
]

# --- TIPAGEM ---
COLUNAS_NUMERICAS = {
    'ID': 'int64',
    'Area': 'int64',
    'Quartos': 'int64',
    'Banheiros': 'int64',
    'Vagas garagem': 'int64',
    'Valor condomínio': 'float64',
    'Valor do Aluguel': 'float64',
    'IPTU': 'float64',
    'Seguro': 'float64'
}

COLUNAS_TEXTO = ['Cidade', 'Aceita Animais', 'Mobilhado', 'Tipo Imóvel', 'Bairro', 'Estado']