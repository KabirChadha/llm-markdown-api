# LLM Markdown Reader API

A fast, lightweight Python FastAPI micro-API designed for RapidAPI monetization. It fetches web pages, strips out HTML clutter (`script`, `style`, `form`, `nav`, `footer`, `header`, `svg`, etc.), and converts the core content into clean, LLM-ready Markdown along with character and token estimates.

---

## Features

- **Clean HTML-to-Markdown Conversion**: Uses `BeautifulSoup` and `markdownify` to strip navigation, scripts, styles, forms, SVGs, and boilerplate before converting to ATX-style Markdown.
- **LLM Token Estimation**: Automatically returns `char_count` and `estimated_tokens` (`char_count // 4`) to help manage LLM context windows.
- **Strict Validation & Error Handling**: Validates HTTP/HTTPS URLs via Pydantic (`HttpUrl`) and raises structured HTTP `400` (fetch/timeout error) or `422` (empty content or invalid URL payload) responses.

---

## Quickstart

### 1. Environment Setup

```bash
python -m venv venv
# Windows PowerShell
.\venv\Scripts\Activate.ps1
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Run the Server

```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Interactive OpenAPI documentation is available at:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

---

## API Specification

### 1. Health Check

**Endpoint:** `GET /`

#### Example Request

```bash
curl -X GET http://127.0.0.1:8000/
```

#### Example Response (`200 OK`)

```json
{
  "status": "live",
  "engine": "FastAPI"
}
```

---

### 2. Extract Markdown

**Endpoint:** `POST /extract`

#### Input Payload Schema

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `url` | `string` (HTTP/HTTPS URL) | Yes | Full URL of the webpage to extract (`http://` or `https://`). |

```json
{
  "url": "https://example.com"
}
```

#### Response Schema (`200 OK`)

| Field | Type | Description |
| :--- | :--- | :--- |
| `url` | `string` | Normalized target URL fetched. |
| `title` | `string` | Extracted page title (`<title>` or fallback `<h1>`). |
| `markdown` | `string` | Clean ATX-formatted Markdown of the core page content. |
| `char_count` | `integer` | Total character length of the extracted Markdown. |
| `estimated_tokens` | `integer` | Estimated LLM token count (`char_count // 4`). |

```json
{
  "url": "https://example.com/",
  "title": "Example Domain",
  "markdown": "# Example Domain\n\nThis domain is for use in illustrative examples in documents. You may use this domain in literature without prior coordination or asking for permission.\n\n[More information...](https://www.iana.org/domains/example)",
  "char_count": 233,
  "estimated_tokens": 58
}
```

#### Error Responses

- **`400 Bad Request`**: Network failure, DNS error, timeout, or non-2xx upstream HTTP status.
- **`422 Unprocessable Entity`**: Invalid URL format in payload or extracted page yielded empty content.

#### Example `curl` Request

```bash
curl -X POST http://127.0.0.1:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

