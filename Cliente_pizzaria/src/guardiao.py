import pandas as pd
import config as cfg

def validar_arquivo(df):
    """
    1. Verifica Padronização (Colunas).
    2. Verifica Integridade (>80% linhas preenchidas).
    Retorna: (Sucesso: bool, Mensagem: str)
    """
    
    # 1. VERIFICAÇÃO DE COLUNAS (PADRONIZAÇÃO)
    cols_arquivo = set(df.columns)
    cols_esperadas = set(cfg.COLUNAS_OFICIAIS)
    
    if not cols_esperadas.issubset(cols_arquivo):
        faltantes = cols_esperadas - cols_arquivo
        return False, f"❌ Erro de Padronização: Faltam as colunas {faltantes}"

    # 2. VERIFICAÇÃO DE INTEGRIDADE (REGRA 80%)
    total_linhas = len(df)
    if total_linhas == 0:
        return False, "❌ Arquivo vazio."

    # Conta linhas com nulos
    nulos = df.isnull().any(axis=1).sum()
    pct_integridade = ((total_linhas - nulos) / total_linhas) * 100

    if pct_integridade < 80.0:
        return False, f"❌ REPROVADO: Integridade crítica ({pct_integridade:.2f}%). Mínimo aceitável: 80%."

    return True, f"✅ Aprovado: Integridade de {pct_integridade:.2f}%."