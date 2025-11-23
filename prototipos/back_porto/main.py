from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

import httpx
import pandas as pd
import os
import tempfile
import uuid


# ================== APP + CORS =====================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # por enquanto libera pra qualquer origem
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ================== "AUTENTICAÇÃO DE MENTIRINHA" ==================
SENHA_CORRETA = "porto123"  # você pode trocar essa senha
FUNCOES_PERMITIDAS = {"executivo", "trabalhador", "analista"}


def validar_acesso(senha: str, funcao: str):
    """
    Validação simples:
    - senha tem que bater com SENHA_CORRETA
    - função precisa ser uma das permitidas
    """
    if senha != SENHA_CORRETA:
        raise HTTPException(status_code=401, detail="Senha incorreta.")

    if funcao.lower() not in FUNCOES_PERMITIDAS:
        raise HTTPException(
            status_code=403,
            detail="Função não autorizada. Use: executivo, trabalhador ou analista."
        )


# ================== MODELOS P/ REQUISIÇÕES ==================
class Pergunta(BaseModel):
    senha: str
    funcao: str
    pergunta: str


# ================== LEITURA DOS DADOS ==================
# Caminho da pasta "data"
BASE_PATH = r"/api_porto/data"


def load_csv(name: str) -> pd.DataFrame:
    """
    Lê um arquivo .csv da pasta data.
    Ex.: load_csv("dim_pais") -> lê data/dim_pais.csv
    """
    path = os.path.join(BASE_PATH, f"{name}.csv")
    return pd.read_csv(path)


def montar_df_navios() -> pd.DataFrame:
    fato = load_csv("fato_movimentacao_portuaria")
    porto = load_csv("dim_porto_coord")
    pais = load_csv("dim_pais")
    regiao = load_csv("dim_regiao")
    mare = load_csv("dim_mare")
    porte = load_csv("dim_porte_navio")
    tempo = load_csv("dim_tempo")
    operacao = load_csv("dim_tipo_operacao")

    df = (
        fato
        .merge(porto, on="id_porto")
        .merge(pais, on="id_pais")
        .merge(regiao, on="id_regiao")
        .merge(mare, on="id_mare")
        .merge(porte, on="id_porte")
        .merge(tempo, on="id_tempo")
        .merge(operacao, on="id_tipo_operacao")
    )

    return df


# ================== ROTAS BÁSICAS ==================
@app.get("/")
def root():
    return {"message": "API do Porto funcionando!"}


# 2 e 3) NAVIOS PROTEGIDO POR SENHA + FUNÇÃO
@app.get("/navios")
def get_navios(senha: str, funcao: str):
    """
    Exemplo de uso (no navegador ou frontend):
    GET /navios?senha=porto123&funcao=executivo
    """
    validar_acesso(senha, funcao)  # checa senha e função

    df = montar_df_navios()
    return df.to_dict(orient="records")



class PromptRequest(BaseModel):
    prompt: str

WEBHOOK = "https://labubulabubu.app.n8n.cloud/webhook/66b258cd-91d8-498f-9e50-1cd3664b4651"

@app.post("/correnteza")
async def prompt(prompt: PromptRequest) :
    payload = {
        "prompt": prompt.prompt,
        "source": "fastapi_backend"
    }
