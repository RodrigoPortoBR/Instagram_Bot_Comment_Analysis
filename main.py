"""
Instagram Comment Analyzer Bot
================================
Extrai comentários de um post público do Instagram e gera uma análise
de sentimento e resumo dos principais pontos usando a API da OpenAI.

Uso:
    python main.py <URL_DO_POST>

Exemplo:
    python main.py https://www.instagram.com/p/ABC123/

Configuração:
    Crie um arquivo .env baseado no .env.example com sua OPENAI_API_KEY.
"""
import sys
import os

# Fix Windows console encoding to support emojis and special characters
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.rule import Rule

from config import get_ig_credentials
from scraper import fetch_comments, extract_shortcode
from analyzer import analyze_comments

console = Console(force_terminal=True)

BANNER = r"""
 ___           _           ___                               _
|_ _|_ __  ___| |_ __ _   / __\___  _ __ ___  _ __ ___   ___| |_ ___
 | || '_ \/ __| __/ _` | / /  / _ \| '_ ` _ \| '_ ` _ \ / _ \ __/ __|
 | || | | \__ \ || (_| |/ /__| (_) | | | | | | | | | | |  __/ |_\__ \
|___|_| |_|___/\__\__,_|\____/\___/|_| |_| |_|_| |_| |_|\___|\__|___/

                    A N A L Y Z E R
"""


def save_result(shortcode: str, analysis: str, comment_count: int) -> str:
    """Salva o resultado da análise em um arquivo .txt."""
    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"analise_{shortcode}_{timestamp}.md"
    filepath = results_dir / filename

    header = (
        f"# Análise de Comentários — Instagram\n"
        f"- **Post**: https://www.instagram.com/p/{shortcode}/\n"
        f"- **Data da análise**: {datetime.now().strftime('%d/%m/%Y às %H:%M')}\n"
        f"- **Comentários analisados**: {comment_count}\n\n"
        f"---\n\n"
    )

    filepath.write_text(header + analysis, encoding="utf-8")
    return str(filepath)


def main():
    console.print(BANNER, style="bold cyan")
    console.print(Rule("Instagram Comment Analyzer Bot", style="cyan"))

    # Validar argumentos
    if len(sys.argv) < 2:
        console.print(
            Panel(
                "[bold]Uso:[/bold] python main.py <URL_DO_POST>\n\n"
                "[bold]Exemplo:[/bold]\n"
                "  python main.py https://www.instagram.com/p/ABC123/\n\n"
                "[dim]Certifique-se de ter configurado o arquivo .env com sua OPENAI_API_KEY.[/dim]",
                title="📖 Como usar",
                border_style="yellow",
            )
        )
        sys.exit(1)

    url = sys.argv[1]

    # Validar URL
    try:
        shortcode = extract_shortcode(url)
    except ValueError as e:
        console.print(f"\n[red]❌ {e}[/red]")
        sys.exit(1)

    console.print()

    # === ETAPA 1: Extração ===
    console.print(Rule("Etapa 1: Extração de Comentários", style="blue"))
    ig_user, ig_pass = get_ig_credentials()

    try:
        console.print("🔐 Conectando ao Instagram e analisando post...")
        console.print("[dim]Isso pode demorar alguns instantes...[/dim]")
        
        comments = fetch_comments(url, ig_user, ig_pass)
        
        console.print(f"[green]✅ {len(comments)} comentários extraídos com sucesso![/green]")
    except Exception as e:
        console.print(f"\n[red]❌ Erro na extração: {e}[/red]")
        sys.exit(1)

    if not comments:
        console.print("\n[yellow]Nenhum comentário para analisar. Encerrando.[/yellow]")
        sys.exit(0)

    # === ETAPA 2: Análise ===
    console.print()
    console.print(Rule("Etapa 2: Análise com IA", style="blue"))

    try:
        console.print(f"🤖 Analisando {len(comments)} comentários com a API da OpenAI...")
        analysis = analyze_comments(comments)
        console.print("[green]✅ Análise concluída![/green]")
    except Exception as e:
        console.print(f"\n[red]❌ Erro na análise: {e}[/red]")
        sys.exit(1)

    # === ETAPA 3: Resultados ===
    console.print()
    console.print(Rule("Resultado da Análise", style="green"))
    console.print()
    console.print(Markdown(analysis))
    console.print()

    # Salvar resultado
    filepath = save_result(shortcode, analysis, len(comments))
    console.print(
        Panel(
            f"[green]📁 Resultado salvo em:[/green]\n[bold]{filepath}[/bold]",
            border_style="green",
        )
    )
    console.print()


if __name__ == "__main__":
    main()
