import re
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from markdownify import markdownify as md
from pydantic import BaseModel, HttpUrl

app = FastAPI(
    title="LLM Markdown Reader API",
    description="Extracts clean, LLM-ready Markdown and token estimates from any web URL.",
    version="1.0.0",
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

STRIP_TAGS = [
    "script",
    "style",
    "form",
    "nav",
    "footer",
    "header",
    "svg",
    "noscript",
    "iframe",
    "aside",
]


class ExtractRequest(BaseModel):
    url: HttpUrl


class ExtractResponse(BaseModel):
    url: str
    title: str
    markdown: str
    char_count: int
    estimated_tokens: int


@app.get("/")
def health_check():
    return {"status": "live", "engine": "FastAPI"}


@app.post("/extract", response_model=ExtractResponse)
def extract_markdown(payload: ExtractRequest):
    target_url = str(payload.url)

    try:
        response = requests.get(
            target_url,
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
            timeout=15,
        )
        response.raise_for_status()
    except requests.exceptions.Timeout as exc:
        raise HTTPException(
            status_code=400, detail=f"Request timed out while fetching URL: {target_url}"
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise HTTPException(
            status_code=400, detail=f"Failed to fetch URL ({target_url}): {str(exc)}"
        ) from exc

    soup = BeautifulSoup(response.text, "html.parser")

    # Extract page title before stripping tags
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    if not title:
        h1_tag = soup.find("h1")
        if h1_tag:
            title = h1_tag.get_text(strip=True)

    # Remove noise elements
    for tag in soup(STRIP_TAGS):
        tag.decompose()

    # Locate primary content container (article -> main -> body -> whole document)
    content_node = soup.find("article") or soup.find("main") or soup.find("body") or soup

    raw_markdown = md(
        str(content_node),
        heading_style="ATX",
        strip=STRIP_TAGS,
    )

    # Collapse excessive blank lines and trim whitespace
    cleaned_markdown = re.sub(r"\n{3,}", "\n\n", raw_markdown).strip()

    if not cleaned_markdown:
        raise HTTPException(
            status_code=422,
            detail="Extracted content is empty after removing non-content HTML elements.",
        )

    char_count = len(cleaned_markdown)
    estimated_tokens = char_count // 4

    return ExtractResponse(
        url=target_url,
        title=title,
        markdown=cleaned_markdown,
        char_count=char_count,
        estimated_tokens=estimated_tokens,
    )

