# 🏠 Real Estate Content Generator

An AI-powered system for generating SEO-optimized, multilingual content for real estate property listings. Built with OpenAI's GPT models, this tool automates the creation of high-quality website content that can be dynamically integrated into property listing templates.

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Usage](#-usage)
  - [CLI Interface](#cli-interface)
  - [REST API](#rest-api)
  - [Interactive UI](#interactive-ui)
- [Input/Output Format](#-inputoutput-format)
- [Configuration](#-configuration)
- [Design Decisions](#-design-decisions)
- [SEO Guidelines](#-seo-guidelines)
- [Evaluation Framework](#-evaluation-framework)
- [Limitations & Future Work](#-limitations--future-work)

---

## ✨ Features

### Core Capabilities

- **🌍 Multilingual Support**: Generate content in 5 languages
  - English (en)
  - Portuguese (pt)
  - Spanish (es)
  - French (fr)
  - Italian (it)

- **🎨 Tone Customization**: Adapt content style to target audience
  - **Formal**: Professional, sophisticated language
  - **Friendly**: Warm, approachable tone
  - **Luxury**: Elegant, exclusive descriptions
  - **Investor**: ROI-focused, analytical content

- **📊 SEO Optimization**: Built-in SEO analysis and recommendations
  - Keyword density analysis
  - Meta tag optimization
  - Location-based keyword injection
  - Regional SEO variations (UK, US, PT, ES, FR, IT, BR)

- **📝 Structured Output**: HTML-tagged sections for easy templating
  - `<title>` - Page title (max 60 chars)
  - `<meta name="description">` - SEO snippet (max 155 chars)
  - `<h1>` - Main headline
  - `<section id="description">` - Full description (500-700 chars)
  - `<ul id="key-features">` - 3-5 bullet points
  - `<section id="neighborhood">` - Area information
  - `<p class="call-to-action">` - CTA closing

### Bonus Features

- ✅ Tone customization (formal, friendly, luxury, investor)
- ✅ Multiple languages (EN, PT, ES, FR, IT)
- ✅ Regional SEO variations
- ✅ Content quality evaluation framework
- ✅ Interactive Streamlit UI
- ✅ REST API for integration
- ✅ Batch processing support

---

## 🏗 Architecture

```
src/
├── __init__.py
├── models/
│   ├── property.py      # Input data models (PropertyInput, Location, Features)
│   └── content.py       # Output models (GeneratedContent, sections)
├── generators/
│   ├── base.py          # Abstract generator interface
│   ├── openai_generator.py  # OpenAI GPT implementation
│   └── prompts.py       # Prompt engineering & templates
├── seo/
│   └── optimizer.py     # SEO analysis & scoring
├── evaluation/
│   └── quality.py       # Content quality assessment
├── api/
│   └── main.py          # FastAPI REST API
├── cli.py               # Command-line interface
├── ui.py                # Streamlit interactive UI
└── config.py            # Configuration management
```

### Design Principles

1. **Separation of Concerns**: Models, generators, and evaluation are independent
2. **Strategy Pattern**: Swappable LLM providers (OpenAI, future: Anthropic, local models)
3. **Async-First**: Efficient concurrent processing for batch operations
4. **Validation-Heavy**: Pydantic models ensure data integrity at every layer

---

## 🚀 Installation

### Prerequisites

- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- OpenAI API key

### Setup

```bash
# Clone the repository
cd /home/ubuntu/scamsam/ai_auto

# Install dependencies with uv (creates .venv automatically)
uv sync

# Or install with development tools
uv sync --extra dev

# Set environment variable
export OPENAI_API_KEY="YOUR_KEY_HERE"
```

---

## ⚡ Quick Start

### Generate content using CLI

```bash
# Generate from JSON file
uv run python -m src.cli --input examples/sample_property.json --output output.html

# Generate in Portuguese with formal tone
uv run python -m src.cli --input examples/sample_property.json --language pt --tone formal

# Use mock generator (no API calls, for testing)
uv run python -m src.cli --input examples/sample_property.json --mock --evaluate
```

### Start the API server

```bash
# Start FastAPI server
uv run python -m src.api.main

# Or using uvicorn directly
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Launch interactive UI

```bash
uv run streamlit run src/ui.py
```

---

## 📖 Usage

### CLI Interface

The CLI provides full access to all features:

```bash
# Basic generation
python -m src.cli -i property.json -o content.html

# With evaluation report
python -m src.cli -i property.json -o content.html --evaluate --verbose

# Override language and tone
python -m src.cli -i property.json --language fr --tone luxury

# Different output formats
python -m src.cli -i property.json --format json
python -m src.cli -i property.json --format both

# Use different model
python -m src.cli -i property.json --model gpt-4o-mini --temperature 0.5
```

**CLI Options:**

| Option | Description |
|--------|-------------|
| `-i, --input` | Input JSON file path (required) |
| `-o, --output` | Output file path (default: stdout) |
| `-l, --language` | Language: en, pt, es, fr, it |
| `-t, --tone` | Tone: formal, friendly, luxury, investor |
| `-m, --model` | OpenAI model (default: gpt-4o) |
| `--temperature` | Generation temperature (default: 0.7) |
| `--mock` | Use mock generator (no API calls) |
| `-e, --evaluate` | Include evaluation report |
| `-f, --format` | Output format: html, json, both |
| `-v, --verbose` | Verbose output |

### REST API

Start the server and access documentation at `http://localhost:8000/docs`

**Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/generate` | Generate content for single property |
| POST | `/batch` | Generate content for multiple properties |
| POST | `/evaluate` | Evaluate existing content |
| GET | `/languages` | List supported languages |
| GET | `/tones` | List available tones |
| GET | `/schema/property` | Get input JSON schema |

**Example Request:**

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "property_data": {
      "title": "T3 apartment in Lisbon",
      "location": {"city": "Lisbon", "neighborhood": "Campo de Ourique"},
      "features": {"bedrooms": 3, "bathrooms": 2, "area_sqm": 120, "balcony": true, "elevator": true},
      "price": 650000,
      "listing_type": "sale",
      "language": "en",
      "tone": "friendly"
    },
    "evaluate": true
  }'
```

### Interactive UI

The Streamlit UI provides a user-friendly interface for:

- Property data input with form fields
- Language and tone selection
- Real-time content generation
- Visual evaluation reports with scores
- HTML/JSON preview and download

```bash
streamlit run src/ui.py
```

---

## 📄 Input/Output Format

### Input JSON Schema

```json
{
  "title": "T3 apartment in Lisbon",
  "location": {
    "city": "Lisbon",
    "neighborhood": "Campo de Ourique",
    "region": "Lisboa",
    "country": "Portugal"
  },
  "features": {
    "bedrooms": 3,
    "bathrooms": 2,
    "area_sqm": 120,
    "balcony": true,
    "parking": false,
    "elevator": true,
    "floor": 2,
    "year_built": 2005,
    "garden": false,
    "pool": false,
    "terrace": false,
    "air_conditioning": false,
    "heating": false,
    "furnished": false,
    "renovated": false,
    "energy_rating": "B"
  },
  "price": 650000,
  "currency": "EUR",
  "listing_type": "sale",
  "language": "en",
  "tone": "friendly",
  "region_seo": "pt",
  "description_extra": "Additional details...",
  "highlights": ["Near metro station", "Recently renovated kitchen"]
}
```

### Output HTML

```html
<title>T3 Apartment for Sale in Campo de Ourique, Lisbon</title>

<meta name="description" content="Spacious 3-bedroom apartment in Lisbon with balcony and elevator, located in Campo de Ourique. Ideal for families.">

<h1>Modern T3 Apartment with Balcony in Campo de Ourique, Lisbon</h1>

<section id="description">
  <p>Located in the charming neighborhood of Campo de Ourique, this elegant T3 apartment offers 120 sqm of bright and spacious living...</p>
</section>

<ul id="key-features">
  <li>120 sqm of living space</li>
  <li>3 bedrooms and 2 bathrooms</li>
  <li>Private balcony</li>
  <li>Elevator access</li>
  <li>Located in Campo de Ourique, Lisbon</li>
</ul>

<section id="neighborhood">
  <p>Campo de Ourique is one of Lisbon's most desirable neighborhoods, known for its vibrant cafés, green parks, and excellent schools.</p>
</section>

<p class="call-to-action">Don't miss this opportunity—schedule your viewing today and discover your new home in Lisbon.</p>
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | (required) |
| `OPENAI_MODEL` | Model to use | gpt-4o |
| `OPENAI_TEMPERATURE` | Generation temperature | 0.7 |
| `OPENAI_MAX_RETRIES` | Max retry attempts | 3 |
| `API_HOST` | API server host | 0.0.0.0 |
| `API_PORT` | API server port | 8000 |
| `API_DEBUG` | Enable debug mode | false |
| `DEFAULT_LANGUAGE` | Default language | en |
| `DEFAULT_TONE` | Default tone | friendly |

### Using .env file

```bash
# Create .env file
cat > .env << EOF
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
OPENAI_TEMPERATURE=0.7
EOF
```

---

## 🎯 Design Decisions

### 1. Model Selection: GPT-4o

**Why GPT-4o?**
- Best multilingual capabilities across supported languages
- Structured output support (JSON schema) ensures consistent responses
- Optimal balance of quality and cost for content generation
- Superior understanding of SEO requirements and real estate context

**Trade-offs:**
- Higher cost than GPT-4o-mini (~$0.008 per property vs ~$0.001)
- Slightly higher latency (~2-3s vs ~1s)

**Mitigation:**
- Batch processing option for cost optimization
- Mock generator for development/testing
- Model selection configurable per request

### 2. Prompt Engineering Strategy

**Approach:**
- **System prompt**: Sets role, language, tone, and constraints
- **User prompt**: Provides structured property data
- **JSON schema**: Enforces output structure

**Key Design Choices:**
- Language-specific system prompts for natural output
- Explicit character limits in prompts
- SEO guidelines embedded in system context
- Tone modifiers adjust vocabulary, not structure

### 3. Validation-Heavy Architecture

**Why?**
- LLM outputs can vary despite constraints
- Character limits are critical for SEO
- Invalid content wastes API costs

**Implementation:**
- Pydantic models for input validation
- Post-generation validation with truncation fallbacks
- Retry logic for constraint violations
- Soft validation (warnings) vs hard validation (errors)

### 4. Async/Await Pattern

**Why?**
- API calls are I/O bound
- Batch processing benefits from concurrency
- FastAPI native async support

**Implementation:**
- AsyncOpenAI client
- Semaphore-based concurrency control
- Graceful error handling in batch operations

### 5. SEO as First-Class Citizen

**Why?**
- Primary business value is SEO effectiveness
- Measurable quality dimension
- Language-specific SEO patterns

**Implementation:**
- Dedicated SEO optimizer module
- Language-specific keyword patterns
- Regional variations (UK vs US terminology)
- Scoring system for quality assurance

---

## 📊 SEO Guidelines

### DO ✅

- Include location-based keywords:
  - "apartment for sale in Lisbon"
  - "T3 apartment in Campo de Ourique"
  - "real estate in Portugal"

- Use property type + location combinations naturally

- Include clear calls to action:
  - "Schedule a visit"
  - "Don't miss this opportunity"
  - "Contact us today"

- Optimize title (50-60 chars) and meta description (120-155 chars)

### DON'T ❌

- Keyword stuffing (>3% density)
- Repetitive or robotic language
- Misleading information
- Generic descriptions without property specifics
- All-caps or excessive punctuation

### Regional SEO Variations

| Region | Keywords | Units |
|--------|----------|-------|
| UK | flat, property, estate agent | sq ft |
| US | apartment, condo, realtor | sq ft |
| PT | apartamento, imóvel | m² |
| ES | piso, inmueble | m² |
| FR | appartement, immobilier | m² |
| IT | appartamento, immobile | mq |

---

## 📈 Evaluation Framework

The system includes a comprehensive content quality evaluation:

### Scoring Dimensions

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Structure | 30% | HTML tags, length constraints, section presence |
| SEO | 30% | Keyword usage, meta optimization, density |
| Readability | 20% | Sentence length, complexity, clarity |
| Fluency | 20% | Grammar, language consistency, natural flow |

### Score Interpretation

| Score | Rating | Action |
|-------|--------|--------|
| 80-100 | Excellent | Ready for publication |
| 60-79 | Good | Minor improvements recommended |
| 40-59 | Fair | Review and regenerate |
| 0-39 | Poor | Requires significant revision |

### Example Evaluation Output

```json
{
  "overall_score": 85.3,
  "is_compliant": true,
  "scores": {
    "structure": 95.0,
    "seo": 82.0,
    "readability": 80.0,
    "fluency": 85.0
  },
  "critical_issues": [],
  "warnings": ["Meta description may be too short"],
  "suggestions": ["Include more location-specific keywords"]
}
```

---

## ⚠️ Limitations & Future Work

### Current Limitations

1. **Language Quality**: While multilingual output is supported, native speaker review is recommended for production use

2. **Neighborhood Knowledge**: AI may generate generic neighborhood descriptions; consider providing `description_extra` for specific local details

3. **Rate Limits**: OpenAI API rate limits may affect batch processing speed

4. **Cost**: GPT-4o costs ~$0.008 per property; consider GPT-4o-mini for high-volume use cases

### Future Enhancements

- [ ] Additional languages (German, Dutch, Arabic, Chinese)
- [ ] Image analysis for property photos
- [ ] A/B testing framework for content variations
- [ ] Integration with property management systems
- [ ] Custom fine-tuned models for specific markets
- [ ] Caching layer for repeated similar properties
- [ ] Webhook support for async processing

---

## 🧪 Testing

```bash
# Run tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=src --cov-report=html

# Test with mock generator (no API calls)
uv run python -m src.cli -i examples/sample_property.json --mock --evaluate
```

---

## 📝 License

MIT License - See LICENSE file for details.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

---

## 📞 Support

For questions or issues, please open a GitHub issue or contact the maintainers.

