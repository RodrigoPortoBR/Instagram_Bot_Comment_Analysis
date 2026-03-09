"""
Instagram Comment Analyzer — Web Interface
=============================================
Interface web simples (Flask) para analisar comentários de posts do Instagram.

Uso:
    python app.py

Acesse: http://localhost:5000
"""
import sys
import os
import json
import threading
import time
import uuid
import traceback
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, jsonify, Response
import markdown

from config import get_ig_credentials
from scraper import fetch_comments, extract_shortcode
from analyzer import analyze_comments

app = Flask(__name__)

# Store for analysis jobs (in-memory, simple approach)
jobs = {}


class AnalysisJob:
    """Tracks the state of an analysis job."""

    def __init__(self, url: str):
        self.id = str(uuid.uuid4())[:8]
        self.url = url
        self.status = "starting"  # starting, extracting, analyzing, done, error
        self.progress_message = "Iniciando..."
        self.comment_count = 0
        self.result_markdown = ""
        self.result_html = ""
        self.error = ""
        self.created_at = datetime.now()


def run_analysis(job: AnalysisJob):
    """Run the full analysis pipeline in a background thread."""
    import sys
    import os
    
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    
    try:
        fnull = open(os.devnull, 'w', encoding='utf-8')
        sys.stdout = fnull
        sys.stderr = fnull
    except Exception:
        fnull = None

    try:
        # Step 1: Extract comments
        job.status = "extracting"
        job.progress_message = "Extraindo comentários do Instagram..."

        ig_user, ig_pass = get_ig_credentials()
        comments = fetch_comments(job.url, ig_user, ig_pass)

        job.comment_count = len(comments)

        if not comments:
            job.status = "error"
            job.error = "Nenhum comentário encontrado neste post."
            return

        job.progress_message = f"{len(comments)} comentários extraídos! Analisando..."

        # Step 2: Analyze
        job.status = "analyzing"
        result = analyze_comments(comments)

        # Convert markdown to HTML
        job.result_markdown = result
        job.result_html = markdown.markdown(result, extensions=["tables", "fenced_code"])

        # Save to file
        try:
            shortcode = extract_shortcode(job.url)
            results_dir = Path(__file__).parent / "results"
            results_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = results_dir / f"analise_{shortcode}_{timestamp}.md"

            header = (
                f"# Análise de Comentários — Instagram\n"
                f"- **Post**: {job.url}\n"
                f"- **Data da análise**: {datetime.now().strftime('%d/%m/%Y às %H:%M')}\n"
                f"- **Comentários analisados**: {len(comments)}\n\n---\n\n"
            )
            filepath.write_text(header + result, encoding="utf-8")
        except Exception:
            pass  # Non-critical

        job.status = "done"
        job.progress_message = "Análise concluída!"

    except Exception as e:
        import traceback
        full_trace = traceback.format_exc()
        job.status = "error"
        job.error = f"Error: {str(e)}\n\nTraceback:\n{full_trace}"
        job.progress_message = "Erro na análise."
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        if fnull:
            try:
                fnull.close()
            except Exception:
                pass


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"error": "URL não fornecida"}), 400

    # Validate URL
    try:
        extract_shortcode(url)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    # Create job and start background thread
    job = AnalysisJob(url)
    jobs[job.id] = job

    thread = threading.Thread(target=run_analysis, args=(job,), daemon=True)
    thread.start()

    return jsonify({"job_id": job.id})


@app.route("/status/<job_id>")
def status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job não encontrado"}), 404

    return jsonify({
        "status": job.status,
        "progress_message": job.progress_message,
        "comment_count": job.comment_count,
        "result_html": job.result_html,
        "error": job.error,
    })


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  Instagram Comment Analyzer — Web Interface")
    print("  Acesse: http://localhost:5000")
    print("=" * 60 + "\n")
    app.run(debug=False, port=5000)
