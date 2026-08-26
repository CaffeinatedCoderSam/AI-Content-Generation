"""Tests for content generators."""

import pytest
import asyncio

from src.models.property import (
    PropertyInput,
    Location,
    Features,
    Language,
    Tone,
    ListingType,
)
from src.generators.openai_generator import MockContentGenerator
from src.generators.prompts import PromptBuilder


class TestPromptBuilder:
    """Tests for PromptBuilder."""
    
    @pytest.fixture
    def sample_property(self):
        """Create sample property input."""
        return PropertyInput(
            title="T3 apartment in Lisbon",
            location=Location(city="Lisbon", neighborhood="Campo de Ourique"),
            features=Features(
                bedrooms=3,
                bathrooms=2,
                area_sqm=120,
                balcony=True,
                elevator=True,
                floor=2,
                year_built=2005,
            ),
            price=650000,
            listing_type=ListingType.SALE,
            language=Language.ENGLISH,
            tone=Tone.FRIENDLY,
        )
    
    def test_system_prompt_contains_language(self, sample_property):
        """Test that system prompt includes language instruction."""
        builder = PromptBuilder(sample_property)
        prompt = builder.build_system_prompt()
        
        assert "English" in prompt
        assert "LANGUAGE" in prompt
    
    def test_system_prompt_contains_tone(self, sample_property):
        """Test that system prompt includes tone instruction."""
        builder = PromptBuilder(sample_property)
        prompt = builder.build_system_prompt()
        
        assert "warm" in prompt.lower() or "friendly" in prompt.lower()
    
    def test_user_prompt_contains_property_details(self, sample_property):
        """Test that user prompt includes property details."""
        builder = PromptBuilder(sample_property)
        prompt = builder.build_user_prompt()
        
        assert "Lisbon" in prompt
        assert "Campo de Ourique" in prompt
        assert "3" in prompt  # bedrooms
        assert "120" in prompt  # area
        assert "650" in prompt  # price
    
    def test_prompt_builder_portuguese(self):
        """Test prompt builder for Portuguese."""
        prop = PropertyInput(
            title="Apartamento T3",
            location=Location(city="Lisboa"),
            features=Features(bedrooms=3, bathrooms=2, area_sqm=100),
            price=500000,
            listing_type=ListingType.SALE,
            language=Language.PORTUGUESE,
        )
        
        builder = PromptBuilder(prop)
        system_prompt = builder.build_system_prompt()
        
        assert "Portuguese" in system_prompt
    
    def test_get_seo_keywords(self, sample_property):
        """Test SEO keyword extraction."""
        builder = PromptBuilder(sample_property)
        keywords = builder.get_seo_keywords()
        
        assert any("lisbon" in kw.lower() for kw in keywords)
        assert any("campo de ourique" in kw.lower() for kw in keywords)


class TestMockContentGenerator:
    """Tests for MockContentGenerator."""
    
    @pytest.fixture
    def generator(self):
        """Create mock generator."""
        return MockContentGenerator()
    
    @pytest.fixture
    def sample_property(self):
        """Create sample property input."""
        return PropertyInput(
            title="T3 apartment in Lisbon",
            location=Location(city="Lisbon", neighborhood="Campo de Ourique"),
            features=Features(bedrooms=3, bathrooms=2, area_sqm=120),
            price=650000,
            listing_type=ListingType.SALE,
        )
    
    @pytest.mark.asyncio
    async def test_generate_returns_content(self, generator, sample_property):
        """Test that generate returns valid content."""
        content = await generator.generate(sample_property)
        
        assert content is not None
        assert content.title.content
        assert content.meta_description.content
        assert content.headline.content
        assert len(content.key_features.features) >= 3
    
    @pytest.mark.asyncio
    async def test_generate_includes_location(self, generator, sample_property):
        """Test that generated content includes location."""
        content = await generator.generate(sample_property)
        
        html = content.to_html()
        assert "Lisbon" in html
    
    @pytest.mark.asyncio
    async def test_generate_batch(self, generator, sample_property):
        """Test batch generation."""
        properties = [sample_property, sample_property]
        results = await generator.generate_batch(properties)
        
        assert len(results) == 2
        assert all(r is not None for r in results)
    
    def test_estimate_cost_is_zero(self, generator, sample_property):
        """Test that mock generator has zero cost."""
        cost = generator.estimate_cost(sample_property)
        assert cost == 0.0
    
    @pytest.mark.asyncio
    async def test_increments_call_count(self, generator, sample_property):
        """Test that generator tracks call count."""
        assert generator.call_count == 0
        
        await generator.generate(sample_property)
        assert generator.call_count == 1
        
        await generator.generate(sample_property)
        assert generator.call_count == 2

