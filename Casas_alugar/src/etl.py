import pandas as pd
import os
import config as cfg
import guardiao
import re

def ler_csv_robusto(uploaded_file):
    """Lê CSV, detecta separador e remove colunas Unnamed."""
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-8', sep=',')
        if len(df.columns) < 2: 
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding='utf-8', sep=';')
    except UnicodeDecodeError:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, encoding='latin1', sep=';')
    except Exception as e:
        raise Exception(f"Erro na leitura: {e}")

    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    return df

def limpar_string_numerica(series):
    series = series.astype(str).str.replace(r'[^\d,\.]', '', regex=True)
    return series.str.replace(',', '.', regex=False)

def processar_dados(uploaded_file):
    """
    Lê, limpa, calcula custos e CLASSIFICA POR QUARTIS.
    """
    try:
        # 1. LEITURA
        df = ler_csv_robusto(uploaded_file)

    except Exception as e:
        return False, f"Erro ao ler arquivo: {e}"

    # 2. VALIDAÇÃO
    sucesso, msg = guardiao.validar_arquivo(df)
    if not sucesso:
        return False, msg

    # 3. LIMPEZA E TIPAGEM
    try:
        df_limpo = df.copy()
        
        # A. Numéricos
        for col, dtype in cfg.COLUNAS_NUMERICAS.items():
            if col in df_limpo.columns:
                if df_limpo[col].dtype == 'object':
                    df_limpo[col] = limpar_string_numerica(df_limpo[col])
                df_limpo[col] = pd.to_numeric(df_limpo[col], errors='coerce').fillna(0).astype(dtype)

        # B. Textos (Padronização automática definida no config)
        for col in cfg.COLUNAS_TEXTO:
            if col in df_limpo.columns:
                df_limpo[col] = df_limpo[col].astype(str).str.strip().str.title()
                
        # C. Remove vazios essenciais
        df_limpo = df_limpo.dropna(subset=['Cidade', 'Valor do Aluguel'])

        # 4. ENRIQUECIMENTO
        df_limpo['Custo_Mensal'] = df_limpo['Valor do Aluguel'] + df_limpo['Valor condomínio'] + df_limpo['IPTU'] + df_limpo['Seguro']
        
        df_limpo['Preco_m2'] = df_limpo.apply(lambda x: x['Valor do Aluguel'] / x['Area'] if x['Area'] > 0 else 0, axis=1)

        # --- QUARTIS ---
        labels_quartil = ['1. Econômico (Q1)', '2. Médio Padrão (Q2)', '3. Alto Padrão (Q3)', '4. Luxo/Premium (Q4)']
        try:
            df_limpo['Categoria_Preco'] = pd.qcut(
                df_limpo['Valor do Aluguel'], 
                q=4, 
                labels=labels_quartil,
                duplicates='drop'
            )
        except ValueError:
            df_limpo['Categoria_Preco'] = 'Geral'

        # 5. SALVAMENTO
        os.makedirs(cfg.INPUT_DIR, exist_ok=True)
        df_limpo.to_csv(cfg.ARQUIVO_PROCESSADO, index=False, encoding='utf-8')
        
        return True, f"Sucesso! {len(df_limpo)} imóveis processados."

    except Exception as e:
        return False, f"Erro no processamento lógico: {e}"


def carregar_dados():
    if not os.path.exists(cfg.ARQUIVO_PROCESSADO):
        return None
    try:
        df = pd.read_csv(cfg.ARQUIVO_PROCESSADO)
        return df
    except Exception as e:
        print(f"Erro ao carregar: {e}")
        return None