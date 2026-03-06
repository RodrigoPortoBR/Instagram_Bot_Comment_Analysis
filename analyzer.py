"""
Análise de sentimento e geração de resumo dos comentários usando OpenAI.
"""
from openai import OpenAI
from rich.console import Console

from config import get_openai_key, OPENAI_MODEL, MAX_COMMENTS_PER_BATCH

console = Console()

SYSTEM_PROMPT = """Você é um analista de redes sociais especializado em análise de sentimento e tendências de opinião pública. Você analisa comentários de posts do Instagram e gera insights claros e objetivos em português brasileiro.

Suas análises devem ser:
- Fundamentadas nos comentários reais
- Escritas em português brasileiro natural
- Objetivas e sem julgamento moral
- Focadas nos padrões e temas que emergem dos comentários"""

ANALYSIS_PROMPT = """Analise os seguintes {count} comentários de um post do Instagram.

COMENTÁRIOS:
{comments}

---

Gere a seguinte análise em português brasileiro:

1. **MOOD GERAL**: Classifique o sentimento predominante como um destes: POSITIVO, NEGATIVO, MISTO ou NEUTRO. Justifique em 1-2 frases.

2. **RESUMO**: Escreva um parágrafo de 4-8 frases resumindo os principais pontos, temas e opiniões levantados nos comentários. Seja específico sobre o que as pessoas estão dizendo, cite padrões recorrentes e destaque os pontos mais relevantes.

3. **TÓPICOS PRINCIPAIS**: Liste os 3-7 temas/assuntos mais mencionados nos comentários, cada um com uma breve descrição de como aparecem nos comentários.

4. **DADOS**: Informe a proporção aproximada de comentários positivos, negativos e neutros (em porcentagem).

Formate a resposta exatamente assim:

## 🎭 Mood Geral: [CLASSIFICAÇÃO]
[Justificativa]

## 📝 Resumo
[Parágrafo de resumo]

## 📌 Tópicos Principais
- **[Tópico 1]**: [Descrição]
- **[Tópico 2]**: [Descrição]
...

## 📊 Proporção de Sentimentos
- Positivos: X%
- Negativos: X%
- Neutros: X%"""

MERGE_PROMPT = """Você recebeu análises parciais de diferentes lotes de comentários de um mesmo post do Instagram. Consolide todas as análises em uma única análise final coerente.

ANÁLISES PARCIAIS:
{partial_analyses}

---

Gere a análise consolidada final em português brasileiro, seguindo exatamente este formato:

## 🎭 Mood Geral: [CLASSIFICAÇÃO]
[Justificativa considerando todos os lotes]

## 📝 Resumo
[Parágrafo unificado de 4-8 frases consolidando todos os pontos]

## 📌 Tópicos Principais
- **[Tópico 1]**: [Descrição]
- **[Tópico 2]**: [Descrição]
...

## 📊 Proporção de Sentimentos
- Positivos: X%
- Negativos: X%
- Neutros: X%"""


def _format_comments_for_prompt(comments: list[dict]) -> str:
    """Formata a lista de comentários em texto para o prompt."""
    lines = []
    for i, c in enumerate(comments, 1):
        author = c.get("author", "anônimo")
        text = c.get("text", "").strip()
        if text:
            lines.append(f"{i}. @{author}: {text}")
    return "\n".join(lines)


def _call_openai(messages: list[dict], api_key: str) -> str:
    """Faz uma chamada à API da OpenAI e retorna o texto da resposta."""
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=0.4,
        max_tokens=2000,
    )
    return response.choices[0].message.content


def analyze_comments(comments: list[dict]) -> str:
    """Analisa os comentários e retorna o resultado formatado.

    Se houver mais comentários que MAX_COMMENTS_PER_BATCH,
    divide em batches e depois consolida as análises parciais.

    Returns:
        String com a análise formatada em markdown.
    """
    api_key = get_openai_key()

    # Filtrar comentários vazios
    valid_comments = [c for c in comments if c.get("text", "").strip()]

    if not valid_comments:
        return "Nenhum comentário com texto encontrado para análise."

    # Se couber em um batch, análise direta
    if len(valid_comments) <= MAX_COMMENTS_PER_BATCH:
        formatted = _format_comments_for_prompt(valid_comments)
        prompt = ANALYSIS_PROMPT.format(count=len(valid_comments), comments=formatted)

        return _call_openai(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            api_key=api_key,
        )

    # Dividir em batches
    batches = []
    for i in range(0, len(valid_comments), MAX_COMMENTS_PER_BATCH):
        batches.append(valid_comments[i : i + MAX_COMMENTS_PER_BATCH])

    # Análise parcial de cada batch
    partial_analyses = []
    for idx, batch in enumerate(batches, 1):
        formatted = _format_comments_for_prompt(batch)
        prompt = ANALYSIS_PROMPT.format(count=len(batch), comments=formatted)

        result = _call_openai(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            api_key=api_key,
        )
        partial_analyses.append(f"### Lote {idx} ({len(batch)} comentários)\n{result}")

    # Consolidar análises parciais
    merged_text = "\n\n---\n\n".join(partial_analyses)
    merge_prompt = MERGE_PROMPT.format(partial_analyses=merged_text)

    return _call_openai(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": merge_prompt},
        ],
        api_key=api_key,
    )
