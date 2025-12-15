import os

# ==============================================================================
# CONFIGURAÇÃO - IMOBILIÁRIA IMPULSA (V 2.0 - COM BAIRRO E TIPO)
# ==============================================================================

# --- IDENTIDADE ---
NOME_CLIENTE = "Imobiliária Impulsa"
MOEDA = "R$"

# --- CAMINHOS ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_DIR = os.path.join(BASE_DIR, 'dados', 'input')
ARQUIVO_PROCESSADO = os.path.join(INPUT_DIR, 'imoveis_processados.csv')

# --- DEFINIÇÃO DO SCHEMA ---
# Agora incluindo 'Tipo Imóvel' e 'Bairro'
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
    'Bairro'
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

# Adicionei os novos campos aqui para serem padronizados (Title Case)
COLUNAS_TEXTO = ['Cidade', 'Aceita Animais', 'Mobilhado', 'Tipo Imóvel', 'Bairro']