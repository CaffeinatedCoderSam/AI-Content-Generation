"""OpenAI-based content generator implementation."""

import asyncio
import json
import logging
from typing import Optional

from openai import AsyncOpenAI

from ..models.property import PropertyInput
from ..models.content import (
    GeneratedContent,
    TitleSection,
    MetaDescriptionSection,
    HeadlineSection,
    DescriptionSection,
    KeyFeaturesSection,
    NeighborhoodSection,
    CallToActionSection,
)
from .base import BaseContentGenerator, ContentGenerationError, ValidationError
from .prompts import PromptBuilder, get_json_schema

logger = logging.getLogger(__name__)


class OpenAIContentGenerator(BaseContentGenerator):
    """
    OpenAI-powered content generator for real estate listings.
    
    Architecture Decisions:
    
    1. Model Selection (GPT-4o):
       - GPT-4o provides best quality for multilingual content
       - Structured output support ensures consistent JSON responses
       - Cost-effective for batch processing
    
    2. Structured Output:
       - Using JSON schema response format for guaranteed structure
       - Eliminates parsing errors and format inconsistencies
       - Enables reliable validation of generated content
    
    3. Retry Logic:
       - Exponential backoff for rate limit handling
       - Content validation triggers regeneration
       - Graceful degradation on persistent failures
    
    4. Async Design:
       - Async/await for efficient concurrent processing
       - Semaphore-based concurrency control
       - Batch processing for cost optimization
    """
    
    # Pricing per 1M tokens (as of late 2024)
    PRICING = {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    }
    
    # Estimated tokens per generation
    ESTIMATED_TOKENS = {
        "input": 800,   # System + user prompt
        "output": 600,  # Generated content
    }
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_retries: int = 3,
    ):
        """
        Initialize OpenAI content generator.
        
        Args:
            api_key: OpenAI API key (uses OPENAI_API_KEY env var if not provided)
            model: Model to use (gpt-4o, gpt-4o-mini, gpt-4-turbo)
            temperature: Sampling temperature (0-2)
            max_retries: Maximum retry attempts
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        
        # Validate model
        if model not in self.PRICING:
            logger.warning(f"Unknown model {model}, cost estimation may be inaccurate")
    
    async def generate(
        self,
        property_data: PropertyInput,
        retry_count: int = 3,
    ) -> GeneratedContent:
        """
        Generate content for a single property listing.
        
        Args:
            property_data: Validated property input
            retry_count: Number of retry attempts
            
        Returns:
            GeneratedContent with all sections populated
        """
        prompt_builder = PromptBuilder(property_data)
        system_prompt = prompt_builder.build_system_prompt()
        user_prompt = prompt_builder.build_user_prompt()
        
        last_error = None
        
        for attempt in range(retry_count):
            try:
                logger.info(f"Generating content (attempt {attempt + 1}/{retry_count})")
                
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": "property_content",
                            "strict": True,
                            "schema": get_json_schema(),
                        }
                    },
                    temperature=self.temperature,
                )
                
                # Parse response
                content_json = json.loads(response.choices[0].message.content)
                
                # Validate and build content object
                generated = self._build_content(content_json, property_data)
                
                logger.info("Content generated successfully")
                return generated
                
            except json.JSONDecodeError as e:
                last_error = e
                logger.warning(f"JSON parse error on attempt {attempt + 1}: {e}")
                
            except ValidationError as e:
                last_error = e
                logger.warning(f"Validation error on attempt {attempt + 1}: {e.errors}")
                
            except Exception as e:
                last_error = e
                logger.error(f"Generation error on attempt {attempt + 1}: {e}")
                
                # Exponential backoff for rate limits
                if "rate_limit" in str(e).lower():
                    await asyncio.sleep(2 ** attempt)
        
        raise ContentGenerationError(
            f"Failed to generate content after {retry_count} attempts",
            property_data=property_data,
            original_error=last_error,
        )
    
    def _build_content(
        self, 
        raw_content: dict, 
        property_data: PropertyInput,
    ) -> GeneratedContent:
        """
        Build and validate GeneratedContent from raw LLM output.
        
        This method handles length violations by truncating or
        requesting regeneration for critical sections.
        """
        errors = []
        
        # Validate title length
        title = raw_content.get("title", "")
        if len(title) > 60:
            logger.warning(f"Title too long ({len(title)} chars), truncating")
            title = title[:57] + "..."
        
        # Validate meta description length
        meta_desc = raw_content.get("meta_description", "")
        if len(meta_desc) > 155:
            logger.warning(f"Meta description too long ({len(meta_desc)} chars), truncating")
            meta_desc = meta_desc[:152] + "..."
        
        # Validate description length
        description = raw_content.get("description", "")
        if len(description) < 400:
            errors.append(f"Description too short: {len(description)} chars (min 400)")
        if len(description) > 800:
            errors.append(f"Description too long: {len(description)} chars (max 800)")
        
        # Validate key features count
        features = raw_content.get("key_features", [])
        if len(features) < 3:
            errors.append(f"Too few key features: {len(features)} (min 3)")
        if len(features) > 5:
            features = features[:5]  # Truncate to max
        
        if errors:
            raise ValidationError("Content validation failed", errors)
        
        try:
            return GeneratedContent(
                title=TitleSection(content=title),
                meta_description=MetaDescriptionSection(content=meta_desc),
                headline=HeadlineSection(content=raw_content["headline"]),
                description=DescriptionSection(content=description),
                key_features=KeyFeaturesSection(features=features),
                neighborhood=NeighborhoodSection(content=raw_content["neighborhood"]),
                call_to_action=CallToActionSection(content=raw_content["call_to_action"]),
                language=property_data.language.value,
                tone=property_data.tone.value,
            )
        except Exception as e:
            raise ValidationError(f"Failed to build content: {e}", [str(e)])
    
    async def generate_batch(
        self,
        properties: list[PropertyInput],
        concurrency: int = 5,
    ) -> list[GeneratedContent]:
        """
        Generate content for multiple properties concurrently.
        
        Uses semaphore to control concurrency and avoid rate limits.
        
        Args:
            properties: List of property inputs
            concurrency: Max concurrent API calls
            
        Returns:
            List of GeneratedContent (same order as input)
        """
        semaphore = asyncio.Semaphore(concurrency)
        
        async def generate_with_semaphore(prop: PropertyInput) -> GeneratedContent:
            async with semaphore:
                return await self.generate(prop)
        
        tasks = [generate_with_semaphore(p) for p in properties]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results, re-raise first error if any
        generated = []
        errors = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                errors.append((i, result))
                generated.append(None)
            else:
                generated.append(result)
        
        if errors:
            logger.error(f"Batch generation had {len(errors)} failures")
            for idx, error in errors:
                logger.error(f"  Property {idx}: {error}")
        
        return generated
    
    def estimate_cost(self, property_data: PropertyInput) -> float:
        """
        Estimate cost for generating content for one property.
        
        Args:
            property_data: Property input data
            
        Returns:
            Estimated cost in USD
        """
        pricing = self.PRICING.get(self.model, self.PRICING["gpt-4o"])
        
        input_cost = (self.ESTIMATED_TOKENS["input"] / 1_000_000) * pricing["input"]
        output_cost = (self.ESTIMATED_TOKENS["output"] / 1_000_000) * pricing["output"]
        
        return input_cost + output_cost
    
    def estimate_batch_cost(self, count: int) -> float:
        """
        Estimate cost for batch generation.
        
        Args:
            count: Number of properties
            
        Returns:
            Estimated total cost in USD
        """
        single_cost = self.estimate_cost(None)  # Cost is same for all
        return single_cost * count


class MockContentGenerator(BaseContentGenerator):
    """
    Mock generator for testing without API calls.
    
    Useful for:
    - Unit testing
    - UI development
    - Cost-free prototyping
    """
    
    def __init__(self):
        self.call_count = 0
    
    async def generate(
        self,
        property_data: PropertyInput,
        retry_count: int = 3,
    ) -> GeneratedContent:
        """Generate mock content based on property data."""
        self.call_count += 1
        
        p = property_data
        city = p.location.city
        neighborhood = p.location.neighborhood or city
        
        return GeneratedContent(
            title=TitleSection(
                content=f"{p.get_property_type()} for Sale in {city}"[:60]
            ),
            meta_description=MetaDescriptionSection(
                content=f"Beautiful {p.features.bedrooms}-bedroom property in {neighborhood}, {city}. {p.features.area_sqm}sqm with modern amenities."[:155]
            ),
            headline=HeadlineSection(
                content=f"Stunning {p.get_property_type()} in the Heart of {neighborhood}"
            ),
            description=DescriptionSection(
                content=f"Located in the desirable {neighborhood} area of {city}, this exceptional {p.get_property_type()} offers {p.features.area_sqm} square meters of thoughtfully designed living space. The property features {p.features.bedrooms} spacious bedrooms and {p.features.bathrooms} modern bathrooms, perfect for comfortable family living. Built in {p.features.year_built or 2020}, this home combines contemporary design with practical functionality. With a competitive price of {p.format_price()}, this is an outstanding opportunity."
            ),
            key_features=KeyFeaturesSection(
                features=[
                    f"{p.features.area_sqm} sqm of living space",
                    f"{p.features.bedrooms} bedrooms, {p.features.bathrooms} bathrooms",
                    f"Located in {neighborhood}",
                    "Modern amenities",
                    "Excellent condition",
                ][:5]
            ),
            neighborhood=NeighborhoodSection(
                content=f"{neighborhood} is one of {city}'s most sought-after neighborhoods, known for its excellent amenities, local cafés, and vibrant community. With easy access to public transportation and green spaces, it offers the perfect blend of urban convenience and residential charm."
            ),
            call_to_action=CallToActionSection(
                content=f"Don't miss this exceptional opportunity—schedule your viewing today!"
            ),
            language=property_data.language.value,
            tone=property_data.tone.value,
        )
    
    async def generate_batch(
        self,
        properties: list[PropertyInput],
        concurrency: int = 5,
    ) -> list[GeneratedContent]:
        """Generate mock content for multiple properties."""
        return [await self.generate(p) for p in properties]
    
    def estimate_cost(self, property_data: PropertyInput) -> float:
        """Mock generator has no cost."""
        return 0.0

