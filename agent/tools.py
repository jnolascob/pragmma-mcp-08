"""
Herramientas que conectan LangChain con el servidor MCP
"""
import json
import subprocess
import os
from typing import Any, Dict
from langchain_core.tools import tool

# Ruta al servidor MCP compilado
MCP_SERVER_PATH = os.path.join(
   os.path.dirname(__file__),
   "..",
   "mcp-server",
   "dist",
   "index.js"
)

def call_mcp_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
   """
   Llama a una herramienta del servidor MCP
  
   Args:
       tool_name: Nombre de la herramienta MCP
       arguments: Argumentos para la herramienta
      
   Returns:
       Respuesta de la herramienta como string
   """
   try:
       # Preparar mensaje MCP
       mcp_request = {
           "jsonrpc": "2.0",
           "id": 1,
           "method": "tools/call",
           "params": {
               "name": tool_name,
               "arguments": arguments
           }
       }
      
       # Ejecutar servidor MCP
       process = subprocess.Popen(
           ["node", MCP_SERVER_PATH],
           stdin=subprocess.PIPE,
           stdout=subprocess.PIPE,
           stderr=subprocess.PIPE,
           text=True
       )
      
       # Enviar request y obtener respuesta
       stdout, stderr = process.communicate(
           input=json.dumps(mcp_request) + "\n",
           timeout=10
       )
      
       # Parsear respuesta
       if stdout:
           lines = stdout.strip().split("\n")
           for line in lines:
               try:
                   response = json.loads(line)
                   if "result" in response:
                       content = response["result"]["content"][0]["text"]
                       return content
               except json.JSONDecodeError:
                   continue
      
       return f"Error: No se recibió respuesta válida del servidor MCP"
      
   except subprocess.TimeoutExpired:
       process.kill()
       return "Error: Timeout al comunicarse con el servidor MCP"
   except Exception as e:
       return f"Error al llamar herramienta MCP: {str(e)}"


@tool
def get_stock_price(symbol: str) -> str:
   """
   Obtiene el precio actual y estadísticas de una acción.
  
   Args:
       symbol: Símbolo ticker de la acción (ej: AAPL, TSLA, MSFT)
  
   Returns:
       Información del precio actual, cambio y volumen
   """
   result = call_mcp_tool("get_stock_price", {"symbol": symbol.upper()})
   return result


@tool
def get_stock_info(symbol: str) -> str:
   """
   Obtiene información detallada de una empresa cotizada.
  
   Args:
       symbol: Símbolo ticker de la acción
  
   Returns:
       Información de la empresa: nombre, sector, descripción, capitalización, etc.
   """
   result = call_mcp_tool("get_stock_info", {"symbol": symbol.upper()})
   return result


@tool
def compare_stocks(symbols: str) -> str:
   """
   Compara precios y rendimiento de múltiples acciones.
  
   Args:
       symbols: Símbolos separados por comas (ej: "AAPL,MSFT,GOOGL")
  
   Returns:
       Comparación de precios y cambios porcentuales
   """
   symbol_list = [s.strip().upper() for s in symbols.split(",")]
   result = call_mcp_tool("compare_stocks", {"symbols": symbol_list})
   return result