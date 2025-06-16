# Configuration for LinkedIn Post Analysis LLM Processing
# ========================================================

# Input/Output Files
INPUT_XLS = "charlie posts_parsed BIG .xlsx"  # your Excel file
OUTPUT_FILE = "results.jsonl"                 # will be created/appended

# LLM API Configuration
BASE_URL = "http://localhost:1234/v1"          # LM Studio OpenAI-compat server
API_KEY = ""                                   # API key (leave empty for local LM Studio)
MODEL = "qwen3-32b"                           # e.g. "llama-3.2-1b-instruct" or "gpt-4o-mini"
TEMPERATURE = 0.0
MAX_TOKENS = 4096

# API Settings
REQUEST_TIMEOUT = 300                          # Request timeout in seconds
CONNECTION_TIMEOUT = 10                        # Connection test timeout in seconds

# Alternative API Configurations (uncomment to use)
# ─────────────────────────────────────────────────────

# OpenAI Configuration
# BASE_URL = "https://api.openai.com/v1"
# API_KEY = "sk-your-openai-api-key-here"
# MODEL = "gpt-4o-mini"

# OpenRouter Configuration  
# BASE_URL = "https://openrouter.ai/api/v1"
# API_KEY = "sk-or-v1-your-openrouter-key-here"
# MODEL = "anthropic/claude-3-sonnet"

# Azure OpenAI Configuration
# BASE_URL = "https://your-resource.openai.azure.com/openai/deployments/your-deployment/v1"
# API_KEY = "your-azure-api-key"
# MODEL = "gpt-4" 