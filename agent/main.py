"""
Agente de IA con LangChain y OpenAI para consultar información bursátil
"""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from tools import get_stock_price, get_stock_info, compare_stocks

# Cargar variables de entorno
load_dotenv(dotenv_path=".env")

# Verificar API key
if not os.getenv("OPENAI_API_KEY"):
   raise ValueError("OPENAI_API_KEY no configurada en .env")

# Configurar LLM con OpenAI
llm = ChatOpenAI(
   model="gpt-4o",  # Modelo económico y eficiente
   temperature=0.5,
   max_tokens=4096
)

# Definir herramientas
tools = [
   get_stock_price,
   get_stock_info,
   compare_stocks
]

# Crear prompt personalizado para el agente ReAct
prompt_template = """Eres un asistente experto en mercados financieros y análisis de acciones.
Tienes acceso a herramientas para consultar información actualizada del mercado de valores.

HERRAMIENTAS DISPONIBLES:
{tools}

NOMBRES DE HERRAMIENTAS: {tool_names}

INSTRUCCIONES:
- Usa las herramientas cuando necesites información actualizada sobre acciones
- Para consultas de precio, usa get_stock_price
- Para información detallada de empresas, usa get_stock_info
- Para comparar múltiples acciones, usa compare_stocks
- Proporciona análisis claros y concisos
- Si no estás seguro del símbolo ticker, puedes hacer una suposición razonable (ej: Apple = AAPL)
- Si las herramientas no son suficiente puedes consultar en internet

SÍMBOLOS COMUNES:
- Apple: AAPL
- Microsoft: MSFT
- Google/Alphabet: GOOGL
- Amazon: AMZN
- Tesla: TSLA
- Meta/Facebook: META
- Netflix: NFLX
- NVIDIA: NVDA
- Walmart: WMT
- Disney: DIS

FORMATO DE RESPUESTA (OBLIGATORIO):
Question: la pregunta del usuario
Thought: analizo qué información necesito
Action: la herramienta a usar (debe ser una de: {tool_names})
Action Input: los parámetros para la herramienta
Observation: el resultado de la herramienta
... (puedo repetir Thought/Action/Action Input/Observation varias veces si es necesario)
Thought: Ahora tengo toda la información necesaria y puedo dar una respuesta completa
Final Answer: respuesta completa y bien estructurada para el usuario

IMPORTANTE:
- Siempre usa "Action Input:" (no "Action Input" sin dos puntos)
- El Action debe ser exactamente uno de: {tool_names}
- Después de recibir una Observation, decide si necesitas más información (más acciones) o si puedes dar la respuesta final
- La Final Answer debe ser detallada y útil para el usuario

Pregunta actual: {input}

{agent_scratchpad}"""

prompt = PromptTemplate.from_template(prompt_template)

# Crear agente
agent = create_react_agent(
   llm=llm,
   tools=tools,
   prompt=prompt
)

# Configurar memoria
memory = ConversationBufferMemory(
   memory_key="chat_history",
   return_messages=True,
   output_key="output"
)

# Crear executor del agente
agent_executor = AgentExecutor(
   agent=agent,
   tools=tools,
   memory=memory,
   verbose=True,
   max_iterations=10,
   handle_parsing_errors=True,
   return_intermediate_steps=False,
   early_stopping_method="generate"
)

def chat():
   """Función principal para interactuar con el agente"""
   print("=" * 60)
   print("🤖 Asistente de Inversiones con IA (Powered by OpenAI)")
   print("=" * 60)
   print("\nPuedo ayudarte con información sobre acciones del mercado.")
   print("Ejemplos de preguntas:")
   print("  - ¿Cuál es el precio de Apple?")
   print("  - Dame información sobre Tesla")
   print("  - Compara Microsoft, Apple y Google")
   print("  - ¿Cómo está NVIDIA hoy?")
   print("\nEscribe 'salir' para terminar.\n")
  
   while True:
       try:
           user_input = input("\n💬 Tú: ").strip()
          
           if not user_input:
               continue
              
           if user_input.lower() in ['salir', 'exit', 'quit']:
               print("\n👋 ¡Hasta pronto!")
               break
          
           print("\n🤔 Pensando...\n")
          
           # Invocar agente
           response = agent_executor.invoke({"input": user_input})
          
           print(f"\n🤖 Asistente: {response['output']}\n")
           print("-" * 60)
          
       except KeyboardInterrupt:
           print("\n\n👋 Sesión interrumpida. ¡Hasta pronto!")
           break
       except Exception as e:
           print(f"\n❌ Error: {str(e)}")
           print("Por favor, intenta de nuevo.\n")

if __name__ == "__main__":
   chat()