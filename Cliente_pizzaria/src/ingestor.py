import polars as pl
import os
import json
import tempfile
from datetime import datetime
import config as cfg

# Usa o dicionário definido no config
DIRS = cfg.DIRS

# =========================================================
# ⚡ AGENTE 1: INGESTÃO
# =========================================================
class IngestionAgent:
    @staticmethod
    def processar(uploaded_file):
        nome = uploaded_file.name.lower()
        suffix = os.path.splitext(nome)[1]
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name

        try:
            nulls = ["", " ", "null", "nan", "NaN", "NA", "None"]
            if nome.endswith('.csv'):
                with open(tmp_path, 'r', encoding='utf-8', errors='ignore') as f:
                    sep = ';' if ';' in f.readline() else ','
                lf = pl.scan_csv(tmp_path, separator=sep, null_values=nulls, ignore_errors=True, infer_schema_length=10000)
            elif nome.endswith('.xlsx'):
                lf = pl.read_excel(tmp_path).lazy()
            elif nome.endswith('.json'):
                lf = pl.read_json(tmp_path).lazy()
            else: 
                os.unlink(tmp_path)
                return None, None, "Formato desconhecido"

            total = lf.select(pl.len()).collect().item()
            lf = lf.with_columns(pl.sum_horizontal(pl.all().is_null()).alias("nulos_row"))
            lf_clean = lf.filter(pl.col("nulos_row") == 0).drop("nulos_row")
            
            boas = lf_clean.select(pl.len()).collect().item()
            integridade = boas / total if total > 0 else 0
            stats = {"total": total, "ruins": total - boas, "boas": boas, "pct": round(integridade * 100, 2)}

            if integridade < 0.70:
                os.unlink(tmp_path)
                return None, stats, "REPROVADO"
            
            df_final = lf_clean.collect()
            os.unlink(tmp_path)
            return df_final, stats, "APROVADO"

        except Exception as e:
            if os.path.exists(tmp_path): os.unlink(tmp_path)
            return None, None, str(e)

# =========================================================
# 🧠 AGENTE 2: ENGENHARIA DE RECURSOS (TEXTO-TEXTO FIX)
# =========================================================
class TypeAgent:
    @staticmethod
    def converter_e_enriquecer(df: pl.DataFrame):
        df_novo = df.clone()
        
        # --- PASSO A: CONVERSÃO DE TIPOS ---
        for col in df.columns:
            amostra = df_novo[col].drop_nulls().head(1)
            if amostra.is_empty(): continue
            val_str = str(amostra[0])
            
            if ":" in val_str and len(val_str) <= 8 and not ("/" in val_str or "-" in val_str):
                continue
            elif "/" in val_str or "-" in val_str:
                try:
                    has_time = ":" in val_str
                    if has_time:
                        df_novo = df_novo.with_columns(
                            pl.col(col).str.strptime(pl.Datetime, "%d/%m/%Y %H:%M:%S", strict=False).alias(col)
                        )
                        if df_novo[col].null_count() == df_novo.height:
                             df_novo = df_novo.with_columns(
                                pl.col(col).str.strptime(pl.Datetime, "%Y-%m-%d %H:%M:%S", strict=False).alias(col)
                            )
                    else:
                        df_novo = df_novo.with_columns(
                            pl.col(col).str.strptime(pl.Date, "%d/%m/%Y", strict=False).alias(col)
                        )
                        if df_novo[col].null_count() == df_novo.height:
                             df_novo = df_novo.with_columns(
                                pl.col(col).str.strptime(pl.Date, "%Y-%m-%d", strict=False).alias(col)
                            )
                except: pass
            elif any(c.isdigit() for c in val_str):
                try:
                    df_novo = df_novo.with_columns(
                        pl.col(col).cast(pl.Utf8).str.replace_all("R$| |\\.", "").str.replace(",", ".").cast(pl.Float64, strict=False).fill_null(0)
                    )
                except: pass

        # --- PASSO B: CRIAÇÃO DE NOVAS COLUNAS (FIXO) ---
        cols_temporais = [c for c, t in df_novo.schema.items() if t in (pl.Date, pl.Datetime)]
        
        mapa_dias = {"1": "Segunda", "2": "Terça", "3": "Quarta", "4": "Quinta", "5": "Sexta", "6": "Sábado", "7": "Domingo"}
        mapa_meses = {"1": "01-Jan", "2": "02-Fev", "3": "03-Mar", "4": "04-Abr", "5": "05-Mai", "6": "06-Jun", "7": "07-Jul", "8": "08-Ago", "9": "09-Set", "10": "10-Out", "11": "11-Nov", "12": "12-Dez"}

        for col in cols_temporais:
            exprs = [
                pl.col(col).dt.weekday().cast(pl.Utf8).replace(mapa_dias).alias(f"{col}_dia_sem"),
                pl.col(col).dt.month().cast(pl.Utf8).replace(mapa_meses).alias(f"{col}_mes"),
                pl.col(col).dt.year().alias(f"{col}_ano"),
                (pl.lit("Q") + pl.col(col).dt.quarter().cast(pl.Utf8)).alias(f"{col}_trimestre")
            ]
            
            if df_novo.schema[col] == pl.Datetime:
                exprs.append(pl.col(col).dt.hour().alias(f"{col}_hora"))
            
            df_novo = df_novo.with_columns(exprs)
            
        return df_novo

# =========================================================
# 💾 AGENTE 3: STORAGE
# =========================================================
def salvar_e_notificar(df, filename_orig, stats):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name_clean = os.path.splitext(filename_orig)[0]
    parquet_name = f"{name_clean}_{timestamp}.parquet"
    
    os.makedirs(DIRS['TRUSTED'], exist_ok=True)
    
    path_parquet = os.path.join(DIRS['TRUSTED'], parquet_name)
    df.write_parquet(path_parquet)
    
    flag_data = {"status": "READY", "file_path": path_parquet, "rows": stats['boas'], "generated_at": timestamp}
    path_flag = os.path.join(DIRS['FLAGS'], f"{name_clean}_{timestamp}.json")
    with open(path_flag, 'w') as f: json.dump(flag_data, f)
    return path_parquet, path_flag

# --- WRAPPER PARA O STREAMLIT ---
def salvar_pipeline(uploaded_file):
    df_pl, stats, msg = IngestionAgent.processar(uploaded_file)
    if df_pl is None:
        return False, msg, None
    
    df_enriched = TypeAgent.converter_e_enriquecer(df_pl)
    salvar_e_notificar(df_enriched, uploaded_file.name, stats)
    
    return True, f"Processado com sucesso! {stats['pct']}% de integridade.", stats