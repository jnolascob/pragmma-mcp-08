from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool
from mcp_client import MCPClient
import config

app = FastAPI(title="Stock Agent API")

# Inicializar cliente MCP
mcp_client = MCPClient()

# Crear herramientas desde MCP
def create_mcp_tools():
    tools = []
    mcp_tools = mcp_client.list_tools()
    
    for tool_def in mcp_tools:
        def make_tool_func(tool_name):
            def tool_func(symbol: str) -> str:
                return mcp_client.call_tool(tool_name, {"symbol": symbol})
            return tool_func
        
        tools.append(Tool(
            name=tool_def["name"],
            func=make_tool_func(tool_def["name"]),
            description=tool_def["description"]
        ))
    
    return tools

# Configurar LLM y agente
llm = ChatOpenAI(
    model="gpt-4-turbo-preview",
    temperature=0,
    openai_api_key=config.OPENAI_API_KEY
)

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful financial assistant with access to real-time stock market data.
    
    When users ask about stocks:
    - Use get_stock_price for current prices and quotes
    - Use get_company_overview for company information
    - Provide clear, concise answers
    - Format numbers appropriately (currency, percentages)
    - Explain financial terms if needed
    """),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

tools = create_mcp_tools()
agent = create_openai_functions_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=5,
    handle_parsing_errors=True
)

# Modelos de request/response
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str

# Endpoints
@app.get("/health")
def health_check():
    return {"status": "healthy", "tools": len(tools)}

@app.post("/query", response_model=QueryResponse)
async def query_agent(request: QueryRequest):
    try:
        result = agent_executor.invoke({"input": request.query})
        return QueryResponse(response=result["output"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tools")
def list_tools():
    return {"tools": [{"name": t.name, "description": t.description} for t in tools]}

@app.on_event("shutdown")
def shutdown_event():
    mcp_client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)