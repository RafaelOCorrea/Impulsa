import pandas as pd
import os
import config as cfg
import guardiao

def processar_dados(uploaded_file):
    """
    Lê o arquivo, limpa aspas, aplica tipagem ISO (YYYY-MM-DD) e salva.
    """
    try:
        # 1. LEITURA ROBUSTA
        try:
            df = pd.read_csv(uploaded_file, encoding='utf-8', sep=',')
            # Se separou errado (tudo numa coluna só), tenta ponto e vírgula
            if len(df.columns) < 2: 
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding='utf-8', sep=';')
        except UnicodeDecodeError:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding='latin1', sep=';')

    except Exception as e:
        return False, f"Erro ao ler arquivo: {e}"

    # 2. VALIDAÇÃO (GUARDIÃO)
    sucesso, msg = guardiao.validar_arquivo(df)
    if not sucesso:
        return False, msg

    # 3. DEFINIÇÃO DE TIPOS E LIMPEZA
    try:
        # A. Limpeza de caracteres indesejados (Aspas que vêm no CSV)
        # O CSV enviado tem aspas em torno das datas: "2015-01-01"
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.replace('"', '', regex=False).str.strip()

        # B. Datas (Estratégia Híbrida: Prioridade ISO YYYY-MM-DD)
        for col in cfg.COLUNAS_DATA:
            if col in df.columns:
                # Tenta formato ISO primeiro (2015-01-01) - Padrão do seu arquivo
                iso_dates = pd.to_datetime(df[col], format='%Y-%m-%d', errors='coerce')
                
                # Tenta formato BR depois (01/01/2015) para o que falhou
                br_dates = pd.to_datetime(df[col], format='%d/%m/%Y', errors='coerce')
                
                # Combina: Usa ISO, preenche falhas com BR
                df[col] = iso_dates.fillna(br_dates)

        # C. Numéricos
        for col, dtype in cfg.COLUNAS_NUMERICAS.items():
            if col in df.columns:
                if df[col].dtype == 'object':
                     df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
                if 'int' in dtype:
                    df[col] = df[col].fillna(0).astype(dtype)

        # 4. VERIFICAÇÃO FINAL
        linhas_antes = len(df)
        df_clean = df.dropna(subset=['order_date'])
        linhas_depois = len(df_clean)
        
        perda = linhas_antes - linhas_depois
        
        if df_clean.empty:
            return False, "❌ Erro Crítico: Nenhuma data válida identificada. Verifique o formato YYYY-MM-DD."

        # 5. SALVAMENTO
        os.makedirs(cfg.INPUT_DIR, exist_ok=True)
        df_clean.to_csv(cfg.ARQUIVO_PROCESSADO, index=False, encoding='utf-8')
        
        msg_sucesso = f"Sucesso! {linhas_depois} linhas processadas."
        if perda > 0:
            msg_sucesso += f" (Aviso: {perda} linhas removidas por data inválida)"
            
        return True, msg_sucesso

    except Exception as e:
        return False, f"Erro no processamento: {e}"


def carregar_dados():
    """Lê o arquivo processado para o Dashboard"""
    if not os.path.exists(cfg.ARQUIVO_PROCESSADO):
        return None
    
    try:
        df = pd.read_csv(cfg.ARQUIVO_PROCESSADO)
        
        for col in cfg.COLUNAS_DATA:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
        
        return df
    except Exception as e:
        print(f"Erro ao carregar dados processados: {e}")
        return None