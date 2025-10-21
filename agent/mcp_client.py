import subprocess
import json
from typing import Any, Dict

class MCPClient:
    def __init__(self):
        self.process = subprocess.Popen(
            ["node", "/mcp-server/dist/index.js"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        self.request_id = 0
    
    def _send_request(self, method: str, params: Dict[str, Any] = None) -> Dict:
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }
        
        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()
        
        response_line = self.process.stdout.readline()
        return json.loads(response_line)
    
    def list_tools(self):
        response = self._send_request("tools/list")
        return response.get("result", {}).get("tools", [])
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]):
        response = self._send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })
        
        result = response.get("result", {})
        content = result.get("content", [{}])[0]
        return content.get("text", "")
    
    def close(self):
        if self.process:
            self.process.terminate()
            self.process.wait()