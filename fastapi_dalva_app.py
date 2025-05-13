
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import tempfile
import os

app = FastAPI()

# Libera acesso para o front-end (ex: Netlify)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, substitua por seu domínio Netlify
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def limpar_planilha_icms(df):
    linha_inicio = df[df.iloc[:, 0] == 'Entrada'].index[0] + 3
    df = df.iloc[linha_inicio:].reset_index(drop=True)
    df = df[['Unnamed: 5', 'Unnamed: 6', 'Unnamed: 7']]
    df.columns = ['Número', 'Data de Lançamento', 'Valor']
    df = df.dropna()
    df = df[~df.apply(lambda row: any(str(val).strip().lower() == col.lower() for val, col in zip(row, df.columns)), axis=1)]
    return df

def limpar_planilha_contabil(df):
    linha_colunas = df[df.iloc[:, 0] == 'Data'].index[0]
    df = df.iloc[linha_colunas + 1:].reset_index(drop=True)
    df.columns = df.iloc[0]
    df = df[1:]
    df = df[['Número', 'Data Lanc.', 'Valor']]
    df.columns = ['Número', 'Data de Lançamento', 'Valor']
    df = df.dropna()
    df = df[~df.apply(lambda row: any(str(val).strip().lower() == col.lower() for val, col in zip(row, df.columns)), axis=1)]
    return df

def normalizar_df(df):
    df['Número'] = df['Número'].astype(str).str.zfill(9)
    df['Data de Lançamento'] = pd.to_datetime(df['Data de Lançamento'], dayfirst=True).dt.strftime('%Y-%m-%d')
    df['Valor'] = df['Valor'].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).astype(float)
    return df.sort_values(by=['Número', 'Data de Lançamento', 'Valor']).reset_index(drop=True)

@app.post("/comparar")
async def comparar_planilhas(file1: UploadFile = File(...), file2: UploadFile = File(...)):
    with tempfile.TemporaryDirectory() as tmpdir:
        path1 = os.path.join(tmpdir, file1.filename)
        path2 = os.path.join(tmpdir, file2.filename)
        with open(path1, "wb") as f1, open(path2, "wb") as f2:
            f1.write(await file1.read())
            f2.write(await file2.read())

        df1_raw = pd.read_excel(path1)
        df2_raw = pd.read_excel(path2)

        df_icms = limpar_planilha_icms(df1_raw)
        df_contabil = limpar_planilha_contabil(df2_raw)

        df_icms = normalizar_df(df_icms)
        df_contabil = normalizar_df(df_contabil)

        df_merged = df_icms.merge(df_contabil, how='outer', indicator=True)
        df_div = df_merged[df_merged['_merge'] != 'both']

        output_path = os.path.join(tmpdir, "divergencias.xlsx")
        df_div.to_excel(output_path, index=False)

        return FileResponse(output_path, filename="divergencias.xlsx")
