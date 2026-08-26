"""Tests for SEO optimizer."""

import pytest

from src.models.property import (
    PropertyInput,
    Location,
    Features,
    Language,
    ListingType,
)
from src.models.content import (
    GeneratedContent,
    TitleSection,
    MetaDescriptionSection,
    HeadlineSection,
    DescriptionSection,
    KeyFeaturesSection,
    NeighborhoodSection,
    CallToActionSection,
)
from src.seo.optimizer import SEOOptimizer, SEOAnalysis


class TestSEOOptimizer:
    """Tests for SEOOptimizer."""
    
    @pytest.fixture
    def sample_property(self):
        """Create sample property input."""
        return PropertyInput(
            title="T3 apartment in Lisbon",
            location=Location(city="Lisbon", neighborhood="Campo de Ourique"),
            features=Features(bedrooms=3, bathrooms=2, area_sqm=120),
            price=650000,
            listing_type=ListingType.SALE,
            language=Language.ENGLISH,
        )
    
    @pytest.fixture
    def good_content(self):
        """Create good SEO content."""
        return GeneratedContent(
            title=TitleSection(content="T3 Apartment for Sale in Lisbon"),
            meta_description=MetaDescriptionSection(
                content="Beautiful 3-bedroom apartment for sale in Campo de Ourique, Lisbon. "
                "120 sqm with balcony and elevator. Schedule your viewing today!"
            ),
            headline=HeadlineSection(
                content="Modern 3-Bedroom Apartment for Sale in Campo de Ourique, Lisbon"
            ),
            description=DescriptionSection(
                content="Located in the charming neighborhood of Campo de Ourique, this elegant "
                "3-bedroom apartment offers 120 sqm of bright and spacious living in Lisbon. "
                "Situated on the second floor with elevator access, the apartment features "
                "three bedrooms, two bathrooms, and a private balcony. Built in 2005, it "
                "combines modern amenities with timeless comfort. Priced at €650,000, this "
                "Lisbon property is ideal for families seeking a well-located home."
            ),
            key_features=KeyFeaturesSection(features=[
                "120 sqm living space",
                "3 bedrooms, 2 bathrooms",
                "Private balcony",
                "Elevator access",
                "Campo de Ourique, Lisbon",
            ]),
            neighborhood=NeighborhoodSection(
                content="Campo de Ourique is one of Lisbon's most desirable neighborhoods, "
                "known for its vibrant cafés, green parks, and excellent schools."
            ),
            call_to_action=CallToActionSection(
                content="Don't miss this opportunity—schedule your viewing today!"
            ),
            language="en",
            tone="friendly",
        )
    
    def test_analyze_returns_analysis(self, sample_property, good_content):
        """Test that analyze returns SEOAnalysis."""
        optimizer = SEOOptimizer(sample_property)
        analysis = optimizer.analyze(good_content)
        
        assert isinstance(analysis, SEOAnalysis)
        assert 0 <= analysis.overall_score <= 100
    
    def test_good_content_scores_well(self, sample_property, good_content):
        """Test that well-optimized content scores high."""
        optimizer = SEOOptimizer(sample_property)
        analysis = optimizer.analyze(good_content)
        
        # Good content should score above 70
        assert analysis.overall_score >= 70
    
    def test_detects_missing_location(self, sample_property):
        """Test that missing location is detected."""
        content = GeneratedContent(
            title=TitleSection(content="Beautiful Apartment for Sale"),  # No city
            meta_description=MetaDescriptionSection(
                content="Amazing apartment with great features and modern design. Perfect for families."
            ),
            headline=HeadlineSection(content="Modern Apartment with Balcony"),
            description=DescriptionSection(
                content="A" * 500
            ),
            key_features=KeyFeaturesSection(features=[
                "3 bedrooms",
                "2 bathrooms",
                "120 sqm",
            ]),
            neighborhood=NeighborhoodSection(
                content="Great neighborhood with amenities."
            ),
            call_to_action=CallToActionSection(
                content="Contact us today!"
            ),
            language="en",
            tone="friendly",
        )
        
        optimizer = SEOOptimizer(sample_property)
        analysis = optimizer.analyze(content)
        
        # Should have lower score due to missing location
        assert analysis.title_score < 100
        assert any("location" in r.lower() or "city" in r.lower() 
                   for r in analysis.recommendations)
    
    def test_keywords_found(self, sample_property, good_content):
        """Test that keywords are correctly identified."""
        optimizer = SEOOptimizer(sample_property)
        analysis = optimizer.analyze(good_content)
        
        assert "lisbon" in [k.lower() for k in analysis.keywords_found]
    
    def test_get_suggestions(self, sample_property, good_content):
        """Test suggestion generation."""
        optimizer = SEOOptimizer(sample_property)
        suggestions = optimizer.get_suggestions(good_content)
        
        assert isinstance(suggestions, list)


class TestSEOAnalysis:
    """Tests for SEOAnalysis dataclass."""
    
    def test_is_passing_true(self):
        """Test passing score detection."""
        analysis = SEOAnalysis(
            overall_score=75,
            issues=[],
        )
        assert analysis.is_passing() is True
    
    def test_is_passing_false_low_score(self):
        """Test failing due to low score."""
        analysis = SEOAnalysis(
            overall_score=60,
            issues=[],
        )
        assert analysis.is_passing() is False
    
    def test_is_passing_false_with_issues(self):
        """Test failing due to issues."""
        analysis = SEOAnalysis(
            overall_score=85,
            issues=["Critical issue"],
        )
        assert analysis.is_passing() is False
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        analysis = SEOAnalysis(
            overall_score=80.5,
            title_score=90,
            keywords_found=["lisbon"],
        )
        
        data = analysis.to_dict()
        
        assert data["overall_score"] == 80.5
        assert data["component_scores"]["title"] == 90
        assert "lisbon" in data["keyword_analysis"]["found"]

