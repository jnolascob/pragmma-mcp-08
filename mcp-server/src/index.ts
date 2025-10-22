import express from "express";
import cors from "cors";
import axios from "axios";

const API_KEY = process.env.ALPHAVANTAGE_API_KEY || "";
const PORT = parseInt(process.env.PORT || "3000", 10);

const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// Tools definition
const tools = [
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
];

// Health check endpoint
app.get("/health", (req, res) => {
  res.json({ status: "healthy", tools: tools.length });
});

// List tools endpoint
app.get("/tools", (req, res) => {
  res.json({ tools });
});

// Call tool endpoint
app.post("/tools/call", async (req, res) => {
  const { name, arguments: args } = req.body;

  if (!name || !args) {
    return res.status(400).json({ error: "Missing name or arguments" });
  }

  try {
    let result;

    if (name === "get_stock_price") {
      const response = await axios.get("https://www.alphavantage.co/query", {
        params: {
          function: "GLOBAL_QUOTE",
          symbol: args.symbol,
          apikey: API_KEY
        }
      });
      
      const quote = response.data["Global Quote"];
      
      result = {
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
    } else if (name === "get_company_overview") {
      const response = await axios.get("https://www.alphavantage.co/query", {
        params: {
          function: "OVERVIEW",
          symbol: args.symbol,
          apikey: API_KEY
        }
      });
      
      result = {
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
    } else {
      return res.status(400).json({ error: `Unknown tool: ${name}` });
    }

    res.json(result);
    
  } catch (error: any) {
    res.status(500).json({
      content: [{
        type: "text",
        text: JSON.stringify({ error: error.message })
      }],
      isError: true
    });
  }
});

app.listen(PORT, "0.0.0.0", () => {
  console.log(`MCP Stocks Server running on port ${PORT}`);
});