#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema, } from "@modelcontextprotocol/sdk/types.js";
import axios from "axios";
import dotenv from "dotenv";
import path from "path";
import { fileURLToPath } from "url";
// Cargar variables de entorno
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
// Try to load .env from current directory first, then parent directory
dotenv.config({ path: path.join(__dirname, "../.env") });
// dotenv.config({ path: path.join(__dirname, "../../.env") });
const ALPHAVANTAGE_API_KEY = process.env.ALPHAVANTAGE_API_KEY;
if (!ALPHAVANTAGE_API_KEY) {
    console.error("ERROR: ALPHAVANTAGE_API_KEY no configurada");
    process.exit(1);
}
// Función helper para obtener cotización
async function getStockQuote(symbol) {
    try {
        const response = await axios.get(`https://www.alphavantage.co/query`, {
            params: {
                function: "GLOBAL_QUOTE",
                symbol: symbol.toUpperCase(),
                apikey: ALPHAVANTAGE_API_KEY,
            },
        });
        const quote = response.data["Global Quote"];
        if (!quote || Object.keys(quote).length === 0) {
            throw new Error(`No se encontraron datos para el símbolo ${symbol}`);
        }
        return {
            symbol: quote["01. symbol"],
            price: parseFloat(quote["05. price"]),
            change: parseFloat(quote["09. change"]),
            changePercent: quote["10. change percent"],
            volume: parseInt(quote["06. volume"]),
        };
    }
    catch (error) {
        throw new Error(`Error al obtener cotización: ${error.message}`);
    }
}
// Función helper para obtener información de empresa
async function getStockOverview(symbol) {
    try {
        const response = await axios.get(`https://www.alphavantage.co/query`, {
            params: {
                function: "OVERVIEW",
                symbol: symbol.toUpperCase(),
                apikey: ALPHAVANTAGE_API_KEY,
            },
        });
        const data = response.data;
        if (!data || !data.Symbol) {
            throw new Error(`No se encontró información para el símbolo ${symbol}`);
        }
        return {
            symbol: data.Symbol,
            name: data.Name,
            description: data.Description,
            sector: data.Sector,
            marketCap: data.MarketCapitalization,
            peRatio: data.PERatio,
            dividendYield: data.DividendYield,
        };
    }
    catch (error) {
        throw new Error(`Error al obtener información: ${error.message}`);
    }
}
// Crear servidor MCP
const server = new Server({
    name: "stock-market-server",
    version: "1.0.0",
}, {
    capabilities: {
        tools: {},
    },
});
// Definir herramientas disponibles
const TOOLS = [
    {
        name: "get_stock_price",
        description: "Obtiene el precio actual y estadísticas de una acción. Use el símbolo ticker de la empresa (ej: AAPL para Apple, TSLA para Tesla, MSFT para Microsoft).",
        inputSchema: {
            type: "object",
            properties: {
                symbol: {
                    type: "string",
                    description: "Símbolo ticker de la acción (ej: AAPL, GOOGL, TSLA)",
                },
            },
            required: ["symbol"],
        },
    },
    {
        name: "get_stock_info",
        description: "Obtiene información detallada de una empresa: nombre, descripción, sector, capitalización de mercado, etc.",
        inputSchema: {
            type: "object",
            properties: {
                symbol: {
                    type: "string",
                    description: "Símbolo ticker de la acción",
                },
            },
            required: ["symbol"],
        },
    },
    {
        name: "compare_stocks",
        description: "Compara precios y rendimiento de dos o más acciones. Útil para análisis comparativo.",
        inputSchema: {
            type: "object",
            properties: {
                symbols: {
                    type: "array",
                    items: { type: "string" },
                    description: "Lista de símbolos ticker para comparar (ej: ['AAPL', 'MSFT', 'GOOGL'])",
                },
            },
            required: ["symbols"],
        },
    },
];
// Handler para listar herramientas
server.setRequestHandler(ListToolsRequestSchema, async () => {
    return { tools: TOOLS };
});
// Handler para ejecutar herramientas
server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;
    try {
        if (name === "get_stock_price") {
            const { symbol } = args;
            const quote = await getStockQuote(symbol);
            return {
                content: [
                    {
                        type: "text",
                        text: JSON.stringify({
                            symbol: quote.symbol,
                            price: `$${quote.price.toFixed(2)}`,
                            change: quote.change >= 0 ? `+$${quote.change.toFixed(2)}` : `-$${Math.abs(quote.change).toFixed(2)}`,
                            changePercent: quote.changePercent,
                            volume: quote.volume.toLocaleString(),
                            timestamp: new Date().toISOString(),
                        }, null, 2),
                    },
                ],
            };
        }
        if (name === "get_stock_info") {
            const { symbol } = args;
            const info = await getStockOverview(symbol);
            return {
                content: [
                    {
                        type: "text",
                        text: JSON.stringify({
                            symbol: info.symbol,
                            name: info.name,
                            sector: info.sector,
                            description: info.description.substring(0, 300) + "...",
                            marketCap: `$${(parseInt(info.marketCap) / 1e9).toFixed(2)}B`,
                            peRatio: info.peRatio,
                            dividendYield: info.dividendYield ? `${(parseFloat(info.dividendYield) * 100).toFixed(2)}%` : "N/A",
                        }, null, 2),
                    },
                ],
            };
        }
        if (name === "compare_stocks") {
            const { symbols } = args;
            const comparisons = await Promise.all(symbols.map(async (symbol) => {
                try {
                    const quote = await getStockQuote(symbol);
                    return {
                        symbol: quote.symbol,
                        price: quote.price,
                        change: quote.change,
                        changePercent: quote.changePercent,
                    };
                }
                catch (error) {
                    return {
                        symbol: symbol,
                        error: "No se pudo obtener datos",
                    };
                }
            }));
            return {
                content: [
                    {
                        type: "text",
                        text: JSON.stringify({ stocks: comparisons }, null, 2),
                    },
                ],
            };
        }
        throw new Error(`Herramienta desconocida: ${name}`);
    }
    catch (error) {
        return {
            content: [
                {
                    type: "text",
                    text: `Error: ${error.message}`,
                },
            ],
            isError: true,
        };
    }
});
// Iniciar servidor
async function main() {
    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.error("Stock Market MCP Server iniciado");
}
main().catch((error) => {
    console.error("Error fatal:", error);
    process.exit(1);
});
