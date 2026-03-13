#!/usr/bin/env python3
"""
Servidor MCP local para Power BI.
Expoe ferramentas de acesso a modelos semânticos do Power BI como um servidor MCP stdio.
Usa o Service Principal configurado no projeto para autenticação automática com renovação de token.

Ferramentas expostas:
- execute_dax: Executa uma query DAX em um dataset do Power BI
- list_measures: Lista todas as medidas de um dataset
- list_tables: Lista tabelas de um dataset
- get_dataset_schema: Retorna o schema completo de um dataset
"""

import json
import os
import re
import sys
import time
from typing import Any

import requests

# ------- Configuração -------
TENANT = os.environ.get("SHAREPOINT_TENANT", "")
CLIENT_ID = os.environ.get("SHAREPOINT_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("SHAREPOINT_CLIENT_SECRET", "")
DEFAULT_WORKSPACE_ID = os.environ.get("POWERBI_WORKSPACE_ID", "")
DEFAULT_DATASET_ID = os.environ.get("POWERBI_DATASET_ID", "")

_token: str = ""
_token_expiry: float = 0


def _get_token() -> str:
    """Obtém ou renova o token OAuth via Service Principal."""
    global _token, _token_expiry

    if _token and time.time() < _token_expiry:
        return _token

    url = f"https://login.microsoftonline.com/{TENANT}/oauth2/v2.0/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://analysis.windows.net/powerbi/api/.default",
    }
    resp = requests.post(url, data=data, timeout=10)
    resp.raise_for_status()
    token_data = resp.json()
    _token = token_data["access_token"]
    _token_expiry = time.time() + token_data.get("expires_in", 3600) - 60
    return _token


def _pbi_request(method: str, path: str, json_body=None) -> dict:
    """Executa requisição autenticada na API do Power BI."""
    token = _get_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"https://api.powerbi.com/v1.0/myorg{path}"
    resp = requests.request(method, url, json=json_body, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json() if resp.content else {}


def _execute_dax(workspace_id: str, dataset_id: str, query: str) -> list[dict]:
    """Executa uma query DAX e retorna as linhas resultantes."""
    body = {"queries": [{"query": query}], "serializerSettings": {"includeNulls": True}}
    path = f"/groups/{workspace_id}/datasets/{dataset_id}/executeQueries"
    result = _pbi_request("POST", path, json_body=body)
    tables = result.get("results", [{}])[0].get("tables", [{}])
    return tables[0].get("rows", []) if tables else []


def _extract_html_value(raw: Any) -> str:
    """Extrai o valor de dentro do HTML retornado por medidas visuais do Power BI."""
    if not isinstance(raw, str) or "<" not in raw:
        return str(raw) if raw is not None else ""
    # Busca conteudo da div.cardValor
    m = re.search(r"<div[^>]*class=['\"]cardValor['\"][^>]*>\s*([^<]+?)\s*</div>", raw, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    # Fallback: remove tags e CSS
    sem_tags = re.sub(r"<[^>]+>", "", raw)
    sem_css = re.sub(r"\{[^}]*\}", "", sem_tags)
    return sem_css.strip()


# ------- Handlers das ferramentas MCP -------

def tool_execute_dax(args: dict) -> str:
    """Executa uma query DAX no Power BI."""
    workspace_id = args.get("workspace_id", DEFAULT_WORKSPACE_ID)
    dataset_id = args.get("dataset_id", DEFAULT_DATASET_ID)
    query = args.get("query", "")

    if not query:
        return "Erro: parâmetro 'query' é obrigatório."

    rows = _execute_dax(workspace_id, dataset_id, query)

    if not rows:
        return "Nenhum resultado retornado."

    # Normaliza e formata o resultado como tabela de texto
    output_lines = []
    for i, row in enumerate(rows):
        norm = {}
        for k, v in row.items():
            clean_key = re.sub(r".*\[|\]", "", k).strip()
            clean_val = _extract_html_value(v) if isinstance(v, str) else (str(v) if v is not None else "")
            norm[clean_key] = clean_val
        output_lines.append(f"Linha {i + 1}: {json.dumps(norm, ensure_ascii=False)}")

    return "\n".join(output_lines)


def tool_list_datasets(args: dict) -> str:
    """Lista todos os datasets disponíveis no workspace."""
    workspace_id = args.get("workspace_id", DEFAULT_WORKSPACE_ID)
    result = _pbi_request("GET", f"/groups/{workspace_id}/datasets")
    datasets = result.get("value", [])
    if not datasets:
        return "Nenhum dataset encontrado."
    lines = [f"- {ds['name']} (ID: {ds['id']})" for ds in datasets]
    return f"Datasets no workspace {workspace_id}:\n" + "\n".join(lines)


def tool_get_schema(args: dict) -> str:
    """Retorna o schema completo (tabelas e medidas) de um dataset."""
    workspace_id = args.get("workspace_id", DEFAULT_WORKSPACE_ID)
    dataset_id = args.get("dataset_id", DEFAULT_DATASET_ID)

    # Lista tabelas
    tables_result = _pbi_request("GET", f"/groups/{workspace_id}/datasets/{dataset_id}/tables")
    tables = tables_result.get("value", [])

    # Lista medidas via DAX
    measures_query = """
    EVALUATE
    SELECTCOLUMNS(
        INFO.MEASURES(),
        "Tabela", [TableName],
        "Medida", [Name],
        "Expressao", [Expression],
        "Formato", [FormatString]
    )
    ORDER BY [TableName], [Name]
    """
    try:
        measure_rows = _execute_dax(workspace_id, dataset_id, measures_query)
    except Exception:
        measure_rows = []

    output = []

    output.append(f"=== SCHEMA DO DATASET {dataset_id} ===\n")

    output.append("TABELAS:")
    for t in tables:
        output.append(f"  - {t.get('name', '?')}")
    output.append("")

    if measure_rows:
        output.append("MEDIDAS:")
        current_table = None
        for row in measure_rows:
            tabela = row.get("[Tabela]", row.get("Tabela", ""))
            medida = row.get("[Medida]", row.get("Medida", ""))
            formato = row.get("[Formato]", row.get("Formato", ""))
            if tabela != current_table:
                output.append(f"  [{tabela}]")
                current_table = tabela
            output.append(f"    - {medida}" + (f" (formato: {formato})" if formato else ""))

    return "\n".join(output)


def tool_evaluate_measure(args: dict) -> str:
    """Avalia uma ou mais medidas do Power BI e retorna os valores."""
    workspace_id = args.get("workspace_id", DEFAULT_WORKSPACE_ID)
    dataset_id = args.get("dataset_id", DEFAULT_DATASET_ID)
    measures = args.get("measures", [])

    if not measures:
        return "Erro: parâmetro 'measures' é obrigatório (lista de nomes de medidas)."

    # Monta ROW com todas as medidas
    cols = ", ".join([f'"{m}", [{m}]' for m in measures])
    query = f"EVALUATE ROW({cols})"
    rows = _execute_dax(workspace_id, dataset_id, query)

    if not rows:
        return "Nenhum resultado."

    output = []
    for k, v in rows[0].items():
        clean_key = re.sub(r".*\[|\]", "", k).strip()
        clean_val = _extract_html_value(v) if isinstance(v, str) else str(v)
        output.append(f"  {clean_key}: {clean_val}")

    return "Valores das medidas:\n" + "\n".join(output)


# ------- MCP Protocol stdio handler -------

TOOLS = {
    "execute_dax": {
        "name": "execute_dax",
        "description": "Executa uma query DAX em um dataset do Power BI e retorna os resultados formatados.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "A query DAX a executar"},
                "dataset_id": {
                    "type": "string",
                    "description": "ID do dataset (opcional, usa o padrão se não informado)",
                },
                "workspace_id": {
                    "type": "string",
                    "description": "ID do workspace (opcional, usa o padrão se não informado)",
                },
            },
            "required": ["query"],
        },
    },
    "list_datasets": {
        "name": "list_datasets",
        "description": "Lista todos os datasets disponíveis no workspace do Power BI.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_id": {"type": "string", "description": "ID do workspace (opcional)"},
            },
        },
    },
    "get_schema": {
        "name": "get_schema",
        "description": (
            "Retorna o schema completo de um dataset do Power BI: "
            "tabelas, colunas e medidas com expressões DAX."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "dataset_id": {"type": "string", "description": "ID do dataset"},
                "workspace_id": {"type": "string", "description": "ID do workspace"},
            },
        },
    },
    "evaluate_measure": {
        "name": "evaluate_measure",
        "description": "Avalia uma ou mais medidas do Power BI e retorna seus valores atuais.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "measures": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Lista de nomes de medidas a avaliar "
                        "(ex: ['Card_Inadimplencia_TOTAL', 'Card_QtdAtraso'])"
                    ),
                },
                "dataset_id": {"type": "string", "description": "ID do dataset"},
                "workspace_id": {"type": "string", "description": "ID do workspace"},
            },
            "required": ["measures"],
        },
    },
}

TOOL_HANDLERS = {
    "execute_dax": tool_execute_dax,
    "list_datasets": tool_list_datasets,
    "get_schema": tool_get_schema,
    "evaluate_measure": tool_evaluate_measure,
}


def send(obj: dict):
    """Envia resposta JSON-RPC pelo stdout."""
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def handle(req: dict) -> dict | None:
    """Processa uma requisição MCP e retorna a resposta."""
    method = req.get("method")
    req_id = req.get("id")
    params = req.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "powerbi-mcp", "version": "1.0.0"},
            },
        }

    if method == "initialized":
        return None  # Notificação — sem resposta

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": list(TOOLS.values())},
        }

    if method == "tools/call":
        tool_name = params.get("name", "")
        tool_args = params.get("arguments", {})
        handler = TOOL_HANDLERS.get(tool_name)

        if not handler:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Ferramenta '{tool_name}' não encontrada."},
            }

        try:
            result_text = handler(tool_args)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"content": [{"type": "text", "text": result_text}]},
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32603, "message": f"Erro ao executar '{tool_name}': {e}"},
            }

    # Métodos não suportados
    if req_id is not None:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Método '{method}' não suportado."},
        }
    return None


def main():
    """Loop principal do servidor MCP stdio."""
    sys.stderr.write("[powerbi-mcp] Servidor iniciado.\n")
    sys.stderr.flush()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            req = json.loads(line)
        except json.JSONDecodeError as e:
            send({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": f"Parse error: {e}"}})
            continue

        try:
            response = handle(req)
            if response is not None:
                send(response)
        except Exception as e:
            req_id = req.get("id")
            if req_id is not None:
                send({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32603, "message": str(e)}})


if __name__ == "__main__":
    main()
