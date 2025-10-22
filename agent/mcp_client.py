import requests
import logging
from typing import Any, Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPClient:
    def __init__(self, base_url: str = "http://mcp-server:3000"):
        self.base_url = base_url
        self.initialized = False
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize the MCP connection by checking health"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                self.initialized = True
                logger.info("MCP connection initialized successfully")
            else:
                raise RuntimeError(f"MCP server health check failed: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to initialize MCP connection: {e}")
            raise
    
    def _send_request(self, method: str, params: Dict[str, Any] = None) -> Dict:
        """Send a request to the MCP server"""
        if not self.initialized:
            raise RuntimeError("MCP client not initialized")
        
        try:
            if method == "tools/list":
                response = requests.get(f"{self.base_url}/tools", timeout=10)
                if response.status_code == 200:
                    return {"result": response.json()}
                else:
                    raise RuntimeError(f"Failed to list tools: {response.status_code}")
            elif method == "tools/call":
                response = requests.post(
                    f"{self.base_url}/tools/call", 
                    json=params, 
                    timeout=30
                )
                if response.status_code == 200:
                    return {"result": response.json()}
                else:
                    error_data = response.json() if response.content else {}
                    return {"error": {"message": error_data.get("error", "Unknown error")}}
            else:
                raise RuntimeError(f"Unknown method: {method}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            raise RuntimeError(f"Failed to communicate with MCP server: {e}")
        except Exception as e:
            logger.error(f"Error sending request to MCP server: {e}")
            raise
    
    def list_tools(self):
        """List available tools from the MCP server"""
        try:
            response = self._send_request("tools/list")
            return response.get("result", {}).get("tools", [])
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return []
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]):
        """Call a tool on the MCP server"""
        try:
            response = self._send_request("tools/call", {
                "name": tool_name,
                "arguments": arguments
            })
            
            if "error" in response:
                error_msg = response["error"].get("message", "Unknown error")
                logger.error(f"Tool call error: {error_msg}")
                return f"Error: {error_msg}"
            
            result = response.get("result", {})
            content = result.get("content", [{}])
            if content and len(content) > 0:
                return content[0].get("text", "")
            return "No content returned"
            
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name}: {e}")
            return f"Error calling tool: {str(e)}"
    
    def close(self):
        """Close the MCP connection"""
        self.initialized = False
        logger.info("MCP client closed")