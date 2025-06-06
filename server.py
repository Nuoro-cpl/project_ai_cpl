from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mcp.server.fastmcp import FastMCP
import os
import uvicorn
import sys
import json
import anthropic
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from fastapi.openapi.utils import get_openapi

load_dotenv()

# Importação do módulo drive
try:
    import drive
    print("Módulo drive importado com sucesso", file=sys.stderr)
except ImportError as e:
    print(f"Erro ao importar módulo drive: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    print("AVISO: Chave API do Claude não encontrada!", file=sys.stderr)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

app = FastAPI(
    title="Google Sheets MCP API",
    description="API para gerenciamento completo de planilhas Google Sheets com MCP",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mcp = FastMCP("sheets-agent")

@app.get("/")
async def root():
    return {
        "message": "API de Google Sheets com MCP está funcionando!",
        "version": "1.0.0",
        "features": [
            "Criar planilhas",
            "Listar planilhas",
            "Listar abas",
            "Criar abas",
            "Ler dados",
            "Ler célula específica",
            "Buscar dados",
            "Sobrescrever dados",
            "Adicionar dados",
            "Linguagem natural com Claude"
        ]
    }

# Modelos Pydantic com estrutura corrigida
class CriarPlanilhaRequest(BaseModel):
    nome_planilha: str = Field(description="Nome da planilha a ser criada")
    email_compartilhamento: str = Field(default="compliancenuoropay@gmail.com", description="Email para compartilhamento")

class ListarPlanilhasRequest(BaseModel):
    limite: int = Field(default=20, description="Número máximo de planilhas a listar")

class ListarAbasRequest(BaseModel):
    planilha_id: str = Field(description="ID da planilha no Google Drive")

class LerDadosRequest(BaseModel):
    planilha_id: str = Field(description="ID da planilha no Google Drive")
    nome_aba: str = Field(default="Principal", description="Nome da aba a ser lida")
    intervalo: str = Field(default="", description="Intervalo específico (ex: 'A1:C10'), vazio para ler tudo")
    incluir_cabecalhos: bool = Field(default=True, description="Se deve incluir os cabeçalhos")

class LerCelulaRequest(BaseModel):
    planilha_id: str = Field(description="ID da planilha no Google Drive")
    nome_aba: str = Field(description="Nome da aba")
    celula: str = Field(description="Endereço da célula (ex: 'A1', 'B5')")

class BuscarDadosRequest(BaseModel):
    planilha_id: str = Field(description="ID da planilha no Google Drive")
    nome_aba: str = Field(description="Nome da aba")
    termo_busca: str = Field(description="Termo a ser buscado")
    coluna_busca: Optional[str] = Field(default=None, description="Nome da coluna específica para buscar")

class CriarAbaRequest(BaseModel):
    planilha_id: str = Field(description="ID da planilha no Google Drive")
    nome_aba: str = Field(description="Nome da nova aba")
    linhas: int = Field(default=100, description="Número de linhas na nova aba")
    colunas: int = Field(default=20, description="Número de colunas na nova aba")

class SobrescreverAbaRequest(BaseModel):
    planilha_id: str = Field(description="ID da planilha no Google Drive")
    nome_aba: str = Field(description="Nome da aba a ser sobrescrita")
    dados: List[List[Any]] = Field(description="Lista de listas com os dados")

class AdicionarCelulasRequest(BaseModel):
    planilha_id: str = Field(description="ID da planilha no Google Drive")
    nome_aba: str = Field(description="Nome da aba")
    dados: List[List[Any]] = Field(description="Lista de listas com os dados a serem adicionados")

class NaturalLanguageQuery(BaseModel):
    pergunta: str = Field(description="Pergunta em linguagem natural sobre planilhas")
    contexto: Optional[str] = Field(default=None, description="Contexto adicional para a pergunta")

# Registrar ferramentas MCP
@mcp.tool()
def criar_planilha(nome_planilha: str, email_compartilhamento: str = "compliancenuoropay@gmail.com") -> dict:
    """
    Cria uma nova planilha no Google Drive e a compartilha com o email especificado.
    
    Args:
        nome_planilha: Nome da planilha a ser criada
        email_compartilhamento: Email com quem compartilhar (padrão: compliancenuoropay@gmail.com)
    """
    try:
        return drive.criar_planilha(nome_planilha, email_compartilhamento)
    except Exception as e:
        return {"erro": f"Erro ao criar planilha: {str(e)}"}

@mcp.tool()
def listar_planilhas(limite: int = 20) -> dict:
    """
    Lista todas as planilhas que a conta de serviço tem acesso.
    
    Args:
        limite: Número máximo de planilhas a listar (padrão: 20)
    """
    try:
        return drive.listar_planilhas(limite)
    except Exception as e:
        return {"erro": f"Erro ao listar planilhas: {str(e)}"}

@mcp.tool()
def listar_abas(planilha_id: str) -> dict:
    """
    Lista todas as abas de uma planilha específica.
    
    Args:
        planilha_id: ID da planilha no Google Drive
    """
    try:
        return drive.listar_abas(planilha_id)
    except Exception as e:
        return {"erro": f"Erro ao listar abas: {str(e)}"}

@mcp.tool()
def ler_dados(
    planilha_id: str,
    nome_aba: str = "Principal",
    intervalo: str = "",
    incluir_cabecalhos: bool = True
) -> dict:
    """
    Lê dados de uma aba específica da planilha.
    
    Args:
        planilha_id: ID da planilha no Google Drive
        nome_aba: Nome da aba a ser lida (padrão: "Principal")
        intervalo: Intervalo específico (ex: "A1:C10"), vazio para ler tudo
        incluir_cabecalhos: Se deve incluir os cabeçalhos na primeira linha
    """
    try:
        return drive.ler_dados(planilha_id, nome_aba, intervalo, incluir_cabecalhos)
    except Exception as e:
        return {"erro": f"Erro ao ler dados: {str(e)}"}

@mcp.tool()
def ler_celula(planilha_id: str, nome_aba: str, celula: str) -> dict:
    """
    Lê o valor de uma célula específica.
    
    Args:
        planilha_id: ID da planilha no Google Drive
        nome_aba: Nome da aba
        celula: Endereço da célula (ex: "A1", "B5")
    """
    try:
        return drive.ler_celula(planilha_id, nome_aba, celula)
    except Exception as e:
        return {"erro": f"Erro ao ler célula: {str(e)}"}

@mcp.tool()
def buscar_dados(
    planilha_id: str,
    nome_aba: str,
    termo_busca: str,
    coluna_busca: str = None
) -> dict:
    """
    Busca dados específicos em uma aba.
    
    Args:
        planilha_id: ID da planilha no Google Drive
        nome_aba: Nome da aba
        termo_busca: Termo a ser buscado
        coluna_busca: Nome da coluna específica para buscar (opcional)
    """
    try:
        return drive.buscar_dados(planilha_id, nome_aba, termo_busca, coluna_busca)
    except Exception as e:
        return {"erro": f"Erro ao buscar dados: {str(e)}"}

@mcp.tool()
def criar_aba(planilha_id: str, nome_aba: str, linhas: int = 100, colunas: int = 20) -> dict:
    """
    Cria uma nova aba em uma planilha existente.
    
    Args:
        planilha_id: ID da planilha
        nome_aba: Nome da nova aba
        linhas: Número de linhas na nova aba (padrão: 100)
        colunas: Número de colunas na nova aba (padrão: 20)
    """
    try:
        return drive.criar_nova_aba(planilha_id, nome_aba, linhas, colunas)
    except Exception as e:
        return {"erro": f"Erro ao criar aba: {str(e)}"}

@mcp.tool()
def sobrescrever_aba(planilha_id: str, nome_aba: str, dados: list) -> dict:
    """
    Sobrescreve os dados de uma aba específica.
    
    Args:
        planilha_id: ID da planilha
        nome_aba: Nome da aba a ser sobrescrita
        dados: Lista de dados (lista de listas)
    """
    try:
        return drive.sobrescrever_aba(planilha_id, nome_aba, dados)
    except Exception as e:
        return {"erro": f"Erro ao sobrescrever aba: {str(e)}"}

@mcp.tool()
def adicionar_celulas(planilha_id: str, nome_aba: str, dados: list) -> dict:
    """
    Adiciona dados a uma aba existente, sem sobrescrever dados existentes.
    
    Args:
        planilha_id: ID da planilha
        nome_aba: Nome da aba
        dados: Lista de dados (lista de listas)
    """
    try:
        return drive.adicionar_celulas(planilha_id, nome_aba, dados)
    except Exception as e:
        return {"erro": f"Erro ao adicionar células: {str(e)}"}

# Endpoints da API REST
@app.post("/api/criar_planilha")
async def api_criar_planilha(query: CriarPlanilhaRequest):
    """
    Cria uma nova planilha no Google Drive.
    """
    try:
        result = drive.criar_planilha(query.nome_planilha, query.email_compartilhamento)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/listar_planilhas")
async def api_listar_planilhas(limite: int = 20):
    """
    Lista todas as planilhas disponíveis.
    """
    try:
        result = drive.listar_planilhas(limite)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/listar_abas")
async def api_listar_abas(query: ListarAbasRequest):
    """
    Lista todas as abas de uma planilha específica.
    """
    try:
        result = drive.listar_abas(query.planilha_id)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ler_dados")
async def api_ler_dados(query: LerDadosRequest):
    """
    Lê dados de uma aba específica da planilha.
    """
    try:
        result = drive.ler_dados(
            query.planilha_id, 
            query.nome_aba, 
            query.intervalo, 
            query.incluir_cabecalhos
        )
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ler_celula")
async def api_ler_celula(query: LerCelulaRequest):
    """
    Lê o valor de uma célula específica.
    """
    try:
        result = drive.ler_celula(query.planilha_id, query.nome_aba, query.celula)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/buscar_dados")
async def api_buscar_dados(query: BuscarDadosRequest):
    """
    Busca dados específicos em uma aba.
    """
    try:
        result = drive.buscar_dados(
            query.planilha_id, 
            query.nome_aba, 
            query.termo_busca, 
            query.coluna_busca
        )
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/criar_aba")
async def api_criar_aba(query: CriarAbaRequest):
    """
    Cria uma nova aba em uma planilha existente.
    """
    try:
        result = drive.criar_nova_aba(query.planilha_id, query.nome_aba, query.linhas, query.colunas)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sobrescrever_aba")
async def api_sobrescrever_aba(query: SobrescreverAbaRequest):
    """
    Sobrescreve completamente os dados de uma aba.
    """
    try:
        result = drive.sobrescrever_aba(query.planilha_id, query.nome_aba, query.dados)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/adicionar_celulas")
async def api_adicionar_celulas(query: AdicionarCelulasRequest):
    """
    Adiciona dados a uma aba existente.
    """
    try:
        result = drive.adicionar_celulas(query.planilha_id, query.nome_aba, query.dados)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/perguntar")
async def perguntar(query: NaturalLanguageQuery):
    """
    Processa perguntas em linguagem natural sobre planilhas Google Sheets.
    """
    try:
        if not ANTHROPIC_API_KEY or not client:
            raise HTTPException(status_code=500, detail="Chave API do Claude não configurada")

        system_prompt = (
            "Você é um assistente especializado em Google Sheets. Seu trabalho é transformar perguntas em linguagem natural "
            "em objetos JSON válidos com o formato especificado. Responda SOMENTE com JSON puro. "
            "Sem explicações. Sem formatação Markdown. Sem prefixos ou sufixos. Apenas JSON."
        )

        user_prompt = f"""
Pergunta: {query.pergunta}

Retorne um JSON neste formato:

{{
  "tipo_consulta": "criar_planilha" ou "listar_planilhas" ou "listar_abas" ou "ler_dados" ou "ler_celula" ou "buscar_dados" ou "criar_aba" ou "sobrescrever_aba" ou "adicionar_celulas",
  "parametros": {{}}
}}

PARÂMETROS PARA CADA TIPO:

- criar_planilha: {{"nome_planilha": "string", "email_compartilhamento": "email@exemplo.com"}} (email é opcional)
- listar_planilhas: {{"limite": numero}} (limite é opcional, padrão 20)
- listar_abas: {{"planilha_id": "string"}}
- ler_dados: {{"planilha_id": "string", "nome_aba": "string", "intervalo": "A1:C10", "incluir_cabecalhos": true}} (nome_aba, intervalo e incluir_cabecalhos opcionais)
- ler_celula: {{"planilha_id": "string", "nome_aba": "string", "celula": "A1"}}
- buscar_dados: {{"planilha_id": "string", "nome_aba": "string", "termo_busca": "string", "coluna_busca": "string"}} (coluna_busca opcional)
- criar_aba: {{"planilha_id": "string", "nome_aba": "string", "linhas": numero, "colunas": numero}} (linhas e colunas opcionais)
- sobrescrever_aba: {{"planilha_id": "string", "nome_aba": "string", "dados": [["linha1col1", "linha1col2"], ["linha2col1", "linha2col2"]]}}
- adicionar_celulas: {{"planilha_id": "string", "nome_aba": "string", "dados": [["linha1col1", "linha1col2"]]}}

EXEMPLOS DETALHADOS:
- "Crie uma planilha chamada Vendas 2024" → {{"tipo_consulta": "criar_planilha", "parametros": {{"nome_planilha": "Vendas 2024"}}}}
- "Liste minhas planilhas" → {{"tipo_consulta": "listar_planilhas", "parametros": {{}}}}
- "Liste as abas da planilha abc123" → {{"tipo_consulta": "listar_abas", "parametros": {{"planilha_id": "abc123"}}}}
- "Leia a aba Principal da planilha abc123" → {{"tipo_consulta": "ler_dados", "parametros": {{"planilha_id": "abc123", "nome_aba": "Principal"}}}}
- "Leia as células A1 até C10 da aba Vendas" → {{"tipo_consulta": "ler_dados", "parametros": {{"planilha_id": "abc123", "nome_aba": "Vendas", "intervalo": "A1:C10"}}}}
- "Qual o valor da célula A1 da aba Principal?" → {{"tipo_consulta": "ler_celula", "parametros": {{"planilha_id": "abc123", "nome_aba": "Principal", "celula": "A1"}}}}
- "Busque por 'João' na planilha abc123" → {{"tipo_consulta": "buscar_dados", "parametros": {{"planilha_id": "abc123", "nome_aba": "Principal", "termo_busca": "João"}}}}
- "Busque por 'São Paulo' na coluna Cidade" → {{"tipo_consulta": "buscar_dados", "parametros": {{"planilha_id": "abc123", "nome_aba": "Principal", "termo_busca": "São Paulo", "coluna_busca": "Cidade"}}}}

PALAVRAS-CHAVE PARA IDENTIFICAR TIPOS:
- LEITURA: "leia", "ler", "mostrar", "exibir", "dados", "conteúdo"
- CÉLULA: "célula", "valor da célula", "A1", "B5", etc.
- BUSCAR: "buscar", "procurar", "encontrar", "pesquisar"
- LISTAR: "listar", "mostrar", "abas", "planilhas"
- CRIAR: "criar", "nova planilha", "nova aba"
- ADICIONAR: "adicionar", "inserir", "acrescentar"
- SOBRESCREVER: "sobrescrever", "substituir", "limpar e adicionar"

Apenas o JSON. Nenhuma explicação.
"""

        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1000,
            temperature=0,
            system=system_prompt,
            messages=[{"role": "user", "content": [{"type": "text", "text": user_prompt}]}]
        )

        content = response.content[0].text.strip()
        if "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        parsed_response = json.loads(content)
        tipo_consulta = parsed_response.get("tipo_consulta")
        parametros = parsed_response.get("parametros", {})

        # Executa a função correspondente
        resultado = None
        if tipo_consulta == "criar_planilha":
            resultado = drive.criar_planilha(**parametros)
        elif tipo_consulta == "listar_planilhas":
            resultado = drive.listar_planilhas(**parametros)
        elif tipo_consulta == "listar_abas":
            resultado = drive.listar_abas(**parametros)
        elif tipo_consulta == "ler_dados":
            resultado = drive.ler_dados(**parametros)
        elif tipo_consulta == "ler_celula":
            resultado = drive.ler_celula(**parametros)
        elif tipo_consulta == "buscar_dados":
            resultado = drive.buscar_dados(**parametros)
        elif tipo_consulta == "criar_aba":
            resultado = drive.criar_nova_aba(**parametros)
        elif tipo_consulta == "sobrescrever_aba":
            resultado = drive.sobrescrever_aba(**parametros)
        elif tipo_consulta == "adicionar_celulas":
            resultado = drive.adicionar_celulas(**parametros)
        else:
            raise HTTPException(status_code=400, detail="Tipo de consulta não reconhecido")

        # Gera interpretação amigável do resultado
        interpretacao_response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1500,
            temperature=0.2,
            system="Você é um assistente de Google Sheets. Interprete resultados e forneça uma explicação clara e amigável.",
            messages=[{"role": "user", "content": [{"type": "text", "text": f"Pergunta: {query.pergunta}\n\nResultados:\n{json.dumps(resultado, ensure_ascii=False, indent=2)}"}]}]
        )

        return {
            "pergunta": query.pergunta,
            "tipo_consulta": tipo_consulta,
            "parametros": parametros,
            "resultado_bruto": resultado,
            "interpretacao": interpretacao_response.content[0].text.strip()
        }

    except Exception as e:
        print(f"[Erro geral] {str(e)}", file=sys.stderr)
        raise HTTPException(status_code=500, detail=f"Erro ao processar pergunta: {str(e)}")

# Endpoints de debug e status
@app.get("/debug/status")
async def debug_status():
    """
    Verifica o status das configurações e credenciais.
    """
    try:
        # Verifica se GOOGLE_CREDENTIALS existe
        google_creds = os.getenv("GOOGLE_CREDENTIALS")
        has_google_creds = google_creds is not None

        # Tenta analisar o JSON
        json_valid = False
        creds_info = {}
        if has_google_creds:
            try:
                creds_dict = json.loads(google_creds)
                json_valid = True
                
                # Extrai informações de diagnóstico (sem revelar dados sensíveis)
                if "type" in creds_dict:
                    creds_info["type"] = creds_dict["type"]
                if "project_id" in creds_dict:
                    creds_info["project_id"] = creds_dict["project_id"]
                if "client_email" in creds_dict:
                    creds_info["client_email"] = creds_dict["client_email"]
                if "private_key_id" in creds_dict:
                    creds_info["has_private_key_id"] = True
                if "private_key" in creds_dict:
                    creds_info["has_private_key"] = len(creds_dict["private_key"]) > 100
            except json.JSONDecodeError:
                json_valid = False
        
        # Verifica se ANTHROPIC_API_KEY existe
        claude_key = os.getenv("ANTHROPIC_API_KEY")
        has_claude_key = claude_key is not None

        # Tenta inicializar o cliente drive
        drive_status = "ok" if drive.services else "erro"

        return {
            "status": "funcionando",
            "environment": {
                "has_google_credentials": has_google_creds,
                "google_credentials_valid_json": json_valid,
                "google_credentials_info": creds_info,
                "has_anthropic_api_key": has_claude_key,
                "drive_service_status": drive_status
            },
            "funcionalidades": {
                "criar_planilha": True,
                "listar_planilhas": True,
                "listar_abas": True,
                "ler_dados": True,
                "ler_celula": True,
                "buscar_dados": True,
                "criar_aba": True,
                "sobrescrever_aba": True,
                "adicionar_celulas": True,
                "linguagem_natural": has_claude_key
            }
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/debug/routes")
async def list_routes():
    """
    Lista todas as rotas disponíveis na API.
    """
    routes = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods),
                "name": getattr(route, 'name', 'unnamed')
            })
    return {"routes": routes}

@app.get("/debug/test_drive")
async def test_drive_connection():
    """
    Testa a conexão com os serviços Google Drive/Sheets.
    """
    try:
        # Tenta listar uma planilha para testar a conexão
        result = drive.listar_planilhas(1)
        
        if result.get("sucesso"):
            return {
                "status": "sucesso",
                "mensagem": "Conexão com Google Drive/Sheets funcionando",
                "detalhes": result
            }
        else:
            return {
                "status": "erro",
                "mensagem": "Falha na conexão com Google Drive/Sheets",
                "detalhes": result
            }
    except Exception as e:
        return {
            "status": "erro",
            "mensagem": f"Erro ao testar conexão: {str(e)}"
        }

# Configuração personalizada do OpenAPI
def get_custom_openapi():
    """Personaliza a descrição OpenAPI."""
    if app.openapi_schema:
        return app.openapi_schema
        
    openapi_schema = get_openapi(
        title="Google Sheets MCP API",
        version="1.0.0",
        description="""
        API completa para gerenciamento de planilhas Google Sheets com suporte a MCP (Model Context Protocol).
        
        ## 🚀 Funcionalidades
        - ✅ Criar planilhas
        - ✅ Listar planilhas
        - ✅ Listar abas
        - ✅ **Ler dados completos**
        - ✅ **Ler célula específica**
        - ✅ **Buscar dados**
        - ✅ Criar abas
        - ✅ Sobrescrever dados
        - ✅ Adicionar dados
        - ✅ Linguagem natural com Claude
        
        ## 🔧 Operações de Leitura
        - **Ler dados**: Lê dados completos de uma aba com opções de intervalo e cabeçalhos
        - **Ler célula**: Lê valor específico de uma célula
        - **Buscar dados**: Busca termos específicos nas planilhas
        
        ## 🤖 Linguagem Natural
        Processe comandos em português como:
        - "Leia a aba Principal da planilha XYZ"
        - "Busque por 'João' na planilha ABC"
        - "Qual o valor da célula A1?"
        """,
        routes=app.routes,
    )
    
    # Detecta ambiente automaticamente usando variáveis do Render
    render_external_url = os.getenv("RENDER_EXTERNAL_URL")
    
    if render_external_url:
        # Produção no Render
        openapi_schema["servers"] = [
            {
                "url": render_external_url,
                "description": "Servidor de Produção"
            }
        ]
    else:
        # Desenvolvimento local
        port = int(os.getenv("PORT", 10000))
        openapi_schema["servers"] = [
            {
                "url": f"http://localhost:{port}",
                "description": "Servidor de Desenvolvimento"
            }
        ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

@app.get("/openapi.json")
def custom_openapi_route():
    """Rota para a especificação OpenAPI personalizada."""
    return get_custom_openapi()

# Rota adicional para compatibilidade com MCP
@app.get("/.well-known/openapi.json")
def mcp_openapi():
    """Rota para a especificação OpenAPI no formato exigido pelo MCP."""
    return get_custom_openapi()

# Sobrescreve a função openapi padrão do FastAPI
app.openapi = get_custom_openapi

# Tenta integrar o router do MCP, se disponível
try:
    if hasattr(mcp, 'router'):
        app.include_router(mcp.router, prefix="/mcp")
        print("Router MCP registrado com sucesso", file=sys.stderr)
except Exception as e:
    print(f"Erro ao registrar router MCP: {e}", file=sys.stderr)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    print(f"Iniciando servidor Google Sheets MCP na porta {port}", file=sys.stderr)
    print(f"Documentação disponível em: http://localhost:{port}/docs", file=sys.stderr)
    uvicorn.run(app, host="0.0.0.0", port=port)


