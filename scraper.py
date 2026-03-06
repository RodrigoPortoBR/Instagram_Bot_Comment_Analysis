"""
Extração de comentários de posts públicos do Instagram via instagrapi.
"""
import re
from instagrapi import Client

def extract_shortcode(url: str) -> str:
    """Extrai o shortcode de uma URL do Instagram."""
    patterns = [
        r"instagram\.com/(?:p|reel|tv)/([A-Za-z0-9_-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    raise ValueError(
        f"URL inválida: {url}\n"
        "Formato esperado: https://www.instagram.com/p/SHORTCODE/"
    )

def fetch_comments(url: str, ig_username: str | None = None, ig_password: str | None = None, amount: int = 0) -> list[dict]:
    """Extrai comentários de um post do Instagram usando instagrapi.

    Args:
        url: URL completa do post do Instagram
        ig_username: Username do Instagram (obrigatório para instagrapi)
        ig_password: Password do Instagram (obrigatório para instagrapi)
        amount: Quantidade de comentários para extrair (0 = todos)

    Returns:
        Lista de dicts com {author, text, timestamp, likes}
    """
    if not ig_username or not ig_password:
        raise ValueError("Credenciais do Instagram são obrigatórias para essa extração. Preencha IG_USERNAME e IG_PASSWORD no arquivo .env.")

    shortcode = extract_shortcode(url)

    cl = Client()
    try:
        # Tenta login
        cl.login(ig_username, ig_password)
    except Exception as e:
        raise RuntimeError(f"Falha de autenticação no Instagram: {e}")

    try:
        media_pk = cl.media_pk_from_url(url)
        # Extrai comentários
        raw_comments = cl.media_comments(media_pk, amount=amount)
    except Exception as e:
        raise RuntimeError(f"Não foi possível carregar o post. Erro: {e}\nVerifique se o post ainda está no ar e se não é privado.")

    if not raw_comments:
        return []

    # Extrair os comentários principais
    comments = []
    
    for c in raw_comments:
        comments.append({
            "author": c.user.username if c.user else "anônimo",
            "text": c.text,
            "timestamp": str(c.created_at_utc),
            "likes": getattr(c, 'like_count', 0),
        })

    return comments
