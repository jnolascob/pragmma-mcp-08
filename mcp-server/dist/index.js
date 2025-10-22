import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { ListToolsRequestSchema, CallToolRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import axios from "axios";
const API_KEY = process.env.ALPHAVANTAGE_API_KEY || "";
const server = new Server({ name: "stocks-server", version: "1.0.0" }, { capabilities: { tools: {} } });
server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: [
        {
            name: "get_stock_price",
            description: "Get current stock price and basic quote data",
            inputSchema: {
                type: "object",
                properties: {
                    symbol: { type: "string", description: "Stock ticker symbol (e.g., AAPL, GOOGL)" }
                },
                required: ["symbol"]
            }
        },
        {
            name: "get_company_overview",
            description: "Get detailed company information and fundamentals",
            inputSchema: {
                type: "object",
                properties: {
                    symbol: { type: "string", description: "Stock ticker symbol" }
                },
                required: ["symbol"]
            }
        }
    ]
}));
server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;
    if (!args) {
        throw new Error("Missing arguments");
    }
    try {
        if (name === "get_stock_price") {
            const response = await axios.get("https://www.alphavantage.co/query", {
                params: {
                    function: "GLOBAL_QUOTE",
                    symbol: args.symbol,
                    apikey: API_KEY
                }
            });
            const quote = response.data["Global Quote"];
            return {
                content: [{
                        type: "text",
                        text: JSON.stringify({
                            symbol: quote["01. symbol"],
                            price: quote["05. price"],
                            change: quote["09. change"],
                            changePercent: quote["10. change percent"],
                            volume: quote["06. volume"]
                        }, null, 2)
                    }]
            };
        }
        if (name === "get_company_overview") {
            const response = await axios.get("https://www.alphavantage.co/query", {
                params: {
                    function: "OVERVIEW",
                    symbol: args.symbol,
                    apikey: API_KEY
                }
            });
            return {
                content: [{
                        type: "text",
                        text: JSON.stringify({
                            name: response.data.Name,
                            sector: response.data.Sector,
                            industry: response.data.Industry,
                            marketCap: response.data.MarketCapitalization,
                            peRatio: response.data.PERatio,
                            eps: response.data.EPS,
                            description: response.data.Description?.substring(0, 300)
                        }, null, 2)
                    }]
            };
        }
        throw new Error(`Unknown tool: ${name}`);
    }
    catch (error) {
        return {
            content: [{
                    type: "text",
                    text: JSON.stringify({ error: error.message })
                }],
            isError: true
        };
    }
});
const transport = new StdioServerTransport();
await server.connect(transport);
console.error("MCP Stocks Server running on stdio");
