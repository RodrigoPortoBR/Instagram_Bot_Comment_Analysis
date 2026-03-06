"""
Configuração e carregamento de variáveis de ambiente.
"""
import os
import sys
from dotenv import load_dotenv

# Carrega variáveis do .env (se existir)
load_dotenv()


def get_openai_key() -> str:
    """Retorna a API key da OpenAI ou encerra com erro."""
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key or key == "sk-your-key-here":
        print("\n❌ OPENAI_API_KEY não configurada!")
        print("   Crie um arquivo .env com: OPENAI_API_KEY=sk-...")
        print("   Ou veja o arquivo .env.example como referência.\n")
        sys.exit(1)
    return key


def get_ig_credentials() -> tuple[str | None, str | None]:
    """Retorna credenciais do Instagram (podem ser None)."""
    username = os.getenv("IG_USERNAME", "").strip() or None
    password = os.getenv("IG_PASSWORD", "").strip() or None
    return username, password


# Configurações do OpenAI
OPENAI_MODEL = "gpt-4o-mini"
MAX_COMMENTS_PER_BATCH = 150  # Máximo de comentários por chamada à API
