from __future__ import annotations

import re
from urllib.parse import quote

import requests
from flask import Flask, jsonify, render_template, request
from datetime import datetime
import psutil

@app.route('/healthz')
def health_check():
    return {
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'uptime': time.time() - psutil.boot_time(),
        'memory': psutil.virtual_memory()._asdict()
    }
app = Flask(__name__)

# Wikimedia asks API clients to send a meaningful User-Agent.
# Replace the email/site bit with your own if you deploy this publicly.
HEADERS = {
    "User-Agent": "Cheekypedia/1.0 (student demo; contact: your_email@example.com)"
}

WIKI_ACTION_API = "https://en.wikipedia.org/w/api.php"
WIKI_SUMMARY_API = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"

TOPICS = [
    "Singapore",
    "Evolution",
    "DNA",
    "Photosynthesis",
    "Minecraft",
    "Botany",
    "Art",
    "Wikipedia",
]


def first_paragraph(text: str) -> str:
    """Return the first non-empty paragraph from a Wikipedia extract."""
    if not text:
        return ""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return paragraphs[0] if paragraphs else text.strip()


def resolve_title(query: str) -> str:
    """
    Convert a user search into Wikipedia's best matching article title.
    Example: 'dna' -> 'DNA'.
    """
    params = {
        "action": "opensearch",
        "search": query,
        "limit": 1,
        "namespace": 0,
        "format": "json",
    }
    response = requests.get(WIKI_ACTION_API, params=params, headers=HEADERS, timeout=8)
    response.raise_for_status()
    data = response.json()

    # OpenSearch response shape: [query, [titles], [descriptions], [urls]]
    if len(data) > 1 and data[1]:
        return data[1][0]
    return query


@app.route("/")
def home():
    return render_template("index.html", topics=TOPICS)


@app.route("/search")
def search():
    query = request.args.get("q", "").strip()

    if not query:
        return jsonify({"error": "Please type your search query!"}), 400

    try:
        title = resolve_title(query)
        summary_url = WIKI_SUMMARY_API.format(title=quote(title, safe=""))
        response = requests.get(summary_url, headers=HEADERS, timeout=8)

        if response.status_code == 404:
            return jsonify({"error": f"No Wikipedia article found for '{query}'. Please try again."}), 404

        response.raise_for_status()
        data = response.json()

        paragraph = first_paragraph(data.get("extract", ""))
        if not paragraph:
            return jsonify({"error": "Wikipedia returned the page, but the intro paragraph was empty."}), 502

        page_urls = data.get("content_urls", {}).get("desktop", {})
        thumbnail = data.get("thumbnail") or {}
        original_image = data.get("originalimage") or {}

        return jsonify(
            {
                "query": query,
                "title": data.get("title", title),
                "description": data.get("description", "Wikipedia article"),
                "paragraph": paragraph,
                "page_url": page_urls.get("page", f"https://en.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}"),
                "edit_url": page_urls.get("edit"),
                "thumbnail": thumbnail.get("source") or original_image.get("source"),
                "is_disambiguation": data.get("type") == "disambiguation",
            }
        )

    except requests.Timeout:
        return jsonify({"error": "Wikipedia took too long to reply. Something's wrong."}), 504
    except requests.RequestException:
        return jsonify({"error": "Could not reach Wikipedia API. Check your internet/server connection."}), 502
    except ValueError:
        return jsonify({"error": "Wikipedia did not return a JSON, this is weird."}), 502


if __name__ == "__main__":
    app.run(debug=True)
