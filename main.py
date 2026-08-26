"""FastAPI REST API for real estate content generation."""

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ..models.property import PropertyInput, Language, Tone, ListingType
from ..models.content import GeneratedContent
from ..generators.openai_generator import OpenAIContentGenerator, MockContentGenerator
from ..generators.base import ContentGenerationError
from ..evaluation.quality import ContentEvaluator, EvaluationReport
from ..seo.optimizer import SEOOptimizer
from ..config import get_config, Config

logger = logging.getLogger(__name__)


# ============================================================================
# API Models
# ============================================================================

class GenerateRequest(BaseModel):
    """Request model for content generation."""
    property_data: PropertyInput = Field(..., description="Property input data")
    evaluate: bool = Field(False, description="Include evaluation report")
    use_mock: bool = Field(False, description="Use mock generator (for testing)")


class GenerateResponse(BaseModel):
    """Response model for content generation."""
    success: bool
    html_content: str
    content: dict
    evaluation: Optional[dict] = None
    estimated_cost: float = 0.0
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "html_content": "<title>T3 Apartment for Sale...</title>",
                "content": {
                    "title": "<title>T3 Apartment for Sale...</title>",
                    "meta_description": "<meta name=\"description\" content=\"...\">",
                },
                "evaluation": None,
                "estimated_cost": 0.0085,
            }
        }
    }


class BatchGenerateRequest(BaseModel):
    """Request model for batch content generation."""
    properties: list[PropertyInput] = Field(..., min_length=1, max_length=100)
    concurrency: int = Field(5, ge=1, le=20)
    evaluate: bool = Field(False)


class BatchGenerateResponse(BaseModel):
    """Response model for batch generation."""
    success: bool
    total: int
    successful: int
    failed: int
    results: list[dict]
    total_cost: float = 0.0


class EvaluateRequest(BaseModel):
    """Request model for content evaluation."""
    property_data: PropertyInput
    content: dict = Field(..., description="Generated content to evaluate")


class EvaluateResponse(BaseModel):
    """Response model for content evaluation."""
    success: bool
    report: dict


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    api_configured: bool


# ============================================================================
# Application Setup
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting Real Estate Content Generator API")
    config = get_config()
    app.state.config = config
    
    # Initialize generators
    if config.openai.api_key:
        app.state.generator = OpenAIContentGenerator(
            api_key=config.openai.api_key,
            model=config.openai.model,
            temperature=config.openai.temperature,
        )
        logger.info(f"OpenAI generator initialized with model: {config.openai.model}")
    else:
        app.state.generator = MockContentGenerator()
        logger.warning("No API key configured, using mock generator")
    
    app.state.mock_generator = MockContentGenerator()
    
    yield
    
    # Shutdown
    logger.info("Shutting down API")


def create_app(config: Optional[Config] = None) -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Real Estate Content Generator API",
        description="""
        AI-powered content generation for real estate property listings.
        
        ## Features
        
        - **Multilingual Support**: English, Portuguese, Spanish, French, Italian
        - **Tone Customization**: Formal, Friendly, Luxury, Investor-focused
        - **SEO Optimization**: Built-in SEO analysis and recommendations
        - **Content Evaluation**: Quality scoring and compliance checking
        - **Batch Processing**: Generate content for multiple properties
        
        ## Usage
        
        1. POST to `/generate` with property data to get HTML content
        2. Use `/evaluate` to assess content quality
        3. Use `/batch` for multiple properties
        """,
        version="1.0.0",
        lifespan=lifespan,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    return app


app = create_app()


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Check API health and configuration status."""
    config = get_config()
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        api_configured=bool(config.openai.api_key),
    )


@app.post("/generate", response_model=GenerateResponse, tags=["Generation"])
async def generate_content(request: GenerateRequest):
    """
    Generate SEO-optimized content for a property listing.
    
    ## Request Body
    
    - **property_data**: Complete property information (see schema)
    - **evaluate**: Whether to include evaluation report (default: false)
    - **use_mock**: Use mock generator for testing (default: false)
    
    ## Response
    
    Returns HTML-formatted content with all required sections:
    - Title (max 60 chars)
    - Meta description (max 155 chars)
    - H1 headline
    - Full description (500-700 chars)
    - Key features (3-5 bullet points)
    - Neighborhood summary
    - Call to action
    """
    try:
        # Select generator
        if request.use_mock:
            generator = app.state.mock_generator
        else:
            generator = app.state.generator
        
        # Estimate cost
        estimated_cost = generator.estimate_cost(request.property_data)
        
        # Generate content
        content = await generator.generate(request.property_data)
        
        # Evaluate if requested
        evaluation = None
        if request.evaluate:
            evaluator = ContentEvaluator(request.property_data)
            report = evaluator.evaluate(content)
            evaluation = report.to_dict()
        
        return GenerateResponse(
            success=True,
            html_content=content.to_html(),
            content=content.to_dict(),
            evaluation=evaluation,
            estimated_cost=estimated_cost,
        )
        
    except ContentGenerationError as e:
        logger.error(f"Generation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Content generation failed: {str(e)}",
        )
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}",
        )


@app.post("/batch", response_model=BatchGenerateResponse, tags=["Generation"])
async def batch_generate(request: BatchGenerateRequest):
    """
    Generate content for multiple properties in batch.
    
    ## Request Body
    
    - **properties**: List of property data (max 100)
    - **concurrency**: Max concurrent generations (default: 5)
    - **evaluate**: Include evaluation for each property
    
    ## Response
    
    Returns results for each property with success/failure status.
    """
    try:
        generator = app.state.generator
        
        # Generate batch
        results = await generator.generate_batch(
            request.properties,
            concurrency=request.concurrency,
        )
        
        # Process results
        response_results = []
        successful = 0
        failed = 0
        total_cost = 0.0
        
        for i, (prop, content) in enumerate(zip(request.properties, results)):
            if content is None or isinstance(content, Exception):
                failed += 1
                response_results.append({
                    "index": i,
                    "success": False,
                    "error": str(content) if content else "Unknown error",
                })
            else:
                successful += 1
                total_cost += generator.estimate_cost(prop)
                
                result_data = {
                    "index": i,
                    "success": True,
                    "html_content": content.to_html(),
                    "content": content.to_dict(),
                }
                
                if request.evaluate:
                    evaluator = ContentEvaluator(prop)
                    report = evaluator.evaluate(content)
                    result_data["evaluation"] = report.to_dict()
                
                response_results.append(result_data)
        
        return BatchGenerateResponse(
            success=failed == 0,
            total=len(request.properties),
            successful=successful,
            failed=failed,
            results=response_results,
            total_cost=total_cost,
        )
        
    except Exception as e:
        logger.exception(f"Batch generation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Batch generation failed: {str(e)}",
        )


@app.post("/evaluate", response_model=EvaluateResponse, tags=["Evaluation"])
async def evaluate_content(request: EvaluateRequest):
    """
    Evaluate generated content quality.
    
    ## Request Body
    
    - **property_data**: Property information for context
    - **content**: Generated content to evaluate
    
    ## Response
    
    Returns detailed evaluation report with:
    - Overall score (0-100)
    - Component scores (structure, SEO, readability, fluency)
    - Critical issues
    - Warnings and suggestions
    """
    try:
        # Reconstruct GeneratedContent from dict
        from ..models.content import (
            TitleSection, MetaDescriptionSection, HeadlineSection,
            DescriptionSection, KeyFeaturesSection, NeighborhoodSection,
            CallToActionSection,
        )
        
        content = GeneratedContent(
            title=TitleSection(content=request.content.get("title", "")),
            meta_description=MetaDescriptionSection(
                content=request.content.get("meta_description", "")
            ),
            headline=HeadlineSection(content=request.content.get("headline", "")),
            description=DescriptionSection(
                content=request.content.get("description", "")
            ),
            key_features=KeyFeaturesSection(
                features=request.content.get("key_features", [])
            ),
            neighborhood=NeighborhoodSection(
                content=request.content.get("neighborhood", "")
            ),
            call_to_action=CallToActionSection(
                content=request.content.get("call_to_action", "")
            ),
            language=request.property_data.language.value,
            tone=request.property_data.tone.value,
        )
        
        evaluator = ContentEvaluator(request.property_data)
        report = evaluator.evaluate(content)
        
        return EvaluateResponse(
            success=True,
            report=report.to_dict(),
        )
        
    except Exception as e:
        logger.exception(f"Evaluation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Evaluation failed: {str(e)}",
        )


@app.get("/languages", tags=["Configuration"])
async def list_languages():
    """List supported languages."""
    return {
        "languages": [
            {"code": "en", "name": "English"},
            {"code": "pt", "name": "Portuguese"},
            {"code": "es", "name": "Spanish"},
            {"code": "fr", "name": "French"},
            {"code": "it", "name": "Italian"},
        ]
    }


@app.get("/tones", tags=["Configuration"])
async def list_tones():
    """List available content tones."""
    return {
        "tones": [
            {"code": "formal", "name": "Formal", "description": "Professional and sophisticated"},
            {"code": "friendly", "name": "Friendly", "description": "Warm and approachable"},
            {"code": "luxury", "name": "Luxury", "description": "Elegant and exclusive"},
            {"code": "investor", "name": "Investor", "description": "Analytical and ROI-focused"},
        ]
    }


@app.get("/schema/property", tags=["Configuration"])
async def get_property_schema():
    """Get JSON schema for property input."""
    return PropertyInput.model_json_schema()


# ============================================================================
# Run Server
# ============================================================================

def run_server():
    """Run the API server."""
    import uvicorn
    
    config = get_config()
    uvicorn.run(
        "src.api.main:app",
        host=config.api.host,
        port=config.api.port,
        reload=config.api.debug,
    )


if __name__ == "__main__":
    run_server()

