"""Tests for data models."""

import pytest
from pydantic import ValidationError

from src.models.property import (
    PropertyInput,
    Location,
    Features,
    Language,
    Tone,
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


class TestPropertyInput:
    """Tests for PropertyInput model."""
    
    def test_valid_property_input(self):
        """Test creating a valid property input."""
        prop = PropertyInput(
            title="T3 apartment in Lisbon",
            location=Location(city="Lisbon", neighborhood="Campo de Ourique"),
            features=Features(bedrooms=3, bathrooms=2, area_sqm=120),
            price=650000,
            listing_type=ListingType.SALE,
        )
        
        assert prop.title == "T3 apartment in Lisbon"
        assert prop.location.city == "Lisbon"
        assert prop.features.bedrooms == 3
        assert prop.price == 650000
    
    def test_invalid_price(self):
        """Test that negative price raises validation error."""
        with pytest.raises(ValidationError):
            PropertyInput(
                title="Test",
                location=Location(city="Test"),
                features=Features(bedrooms=2, bathrooms=1, area_sqm=80),
                price=-100,
                listing_type=ListingType.SALE,
            )
    
    def test_get_property_type_english(self):
        """Test property type generation in English."""
        prop = PropertyInput(
            title="Test",
            location=Location(city="Test"),
            features=Features(bedrooms=3, bathrooms=2, area_sqm=100),
            price=500000,
            listing_type=ListingType.SALE,
            language=Language.ENGLISH,
        )
        
        assert "3-bedroom" in prop.get_property_type()
    
    def test_get_property_type_portuguese(self):
        """Test property type generation in Portuguese."""
        prop = PropertyInput(
            title="Test",
            location=Location(city="Test"),
            features=Features(bedrooms=3, bathrooms=2, area_sqm=100),
            price=500000,
            listing_type=ListingType.SALE,
            language=Language.PORTUGUESE,
        )
        
        assert prop.get_property_type() == "T3"
    
    def test_format_price_sale(self):
        """Test price formatting for sale."""
        prop = PropertyInput(
            title="Test",
            location=Location(city="Test"),
            features=Features(bedrooms=2, bathrooms=1, area_sqm=80),
            price=650000,
            listing_type=ListingType.SALE,
        )
        
        formatted = prop.format_price()
        assert "650" in formatted
        assert "€" in formatted
    
    def test_format_price_rent(self):
        """Test price formatting for rent."""
        prop = PropertyInput(
            title="Test",
            location=Location(city="Test"),
            features=Features(bedrooms=2, bathrooms=1, area_sqm=80),
            price=1500,
            listing_type=ListingType.RENT,
            language=Language.ENGLISH,
        )
        
        formatted = prop.format_price()
        assert "/month" in formatted


class TestFeatures:
    """Tests for Features model."""
    
    def test_valid_features(self):
        """Test creating valid features."""
        features = Features(
            bedrooms=3,
            bathrooms=2,
            area_sqm=120,
            balcony=True,
            elevator=True,
        )
        
        assert features.bedrooms == 3
        assert features.balcony is True
    
    def test_invalid_bedrooms(self):
        """Test that negative bedrooms raises error."""
        with pytest.raises(ValidationError):
            Features(bedrooms=-1, bathrooms=1, area_sqm=50)
    
    def test_energy_rating_validation(self):
        """Test energy rating validation."""
        features = Features(
            bedrooms=2,
            bathrooms=1,
            area_sqm=80,
            energy_rating="B",
        )
        assert features.energy_rating == "B"
        
        with pytest.raises(ValidationError):
            Features(
                bedrooms=2,
                bathrooms=1,
                area_sqm=80,
                energy_rating="X",
            )


class TestGeneratedContent:
    """Tests for GeneratedContent model."""
    
    @pytest.fixture
    def sample_content(self):
        """Create sample generated content."""
        return GeneratedContent(
            title=TitleSection(content="T3 Apartment for Sale in Lisbon"),
            meta_description=MetaDescriptionSection(
                content="Beautiful 3-bedroom apartment in Lisbon with modern amenities and great location."
            ),
            headline=HeadlineSection(content="Modern T3 Apartment in Central Lisbon"),
            description=DescriptionSection(
                content="A" * 500  # Minimum length
            ),
            key_features=KeyFeaturesSection(features=[
                "3 bedrooms",
                "2 bathrooms",
                "120 sqm",
            ]),
            neighborhood=NeighborhoodSection(
                content="This is a great neighborhood with many amenities."
            ),
            call_to_action=CallToActionSection(
                content="Schedule your viewing today!"
            ),
            language="en",
            tone="friendly",
        )
    
    def test_to_html(self, sample_content):
        """Test HTML generation."""
        html = sample_content.to_html()
        
        assert "<title>" in html
        assert '<meta name="description"' in html
        assert "<h1>" in html
        assert '<section id="description">' in html
        assert '<ul id="key-features">' in html
        assert '<section id="neighborhood">' in html
        assert 'class="call-to-action"' in html
    
    def test_to_dict(self, sample_content):
        """Test dictionary conversion."""
        data = sample_content.to_dict()
        
        assert "title" in data
        assert "meta_description" in data
        assert "language" in data
        assert "tone" in data


class TestTitleSection:
    """Tests for TitleSection."""
    
    def test_valid_title(self):
        """Test valid title."""
        title = TitleSection(content="T3 Apartment for Sale in Lisbon")
        assert len(title.content) <= 60
    
    def test_title_too_long(self):
        """Test that title over 60 chars raises error."""
        with pytest.raises(ValidationError):
            TitleSection(content="A" * 61)
    
    def test_to_html(self):
        """Test HTML generation."""
        title = TitleSection(content="Test Title")
        assert title.to_html() == "<title>Test Title</title>"


class TestMetaDescriptionSection:
    """Tests for MetaDescriptionSection."""
    
    def test_valid_meta(self):
        """Test valid meta description."""
        meta = MetaDescriptionSection(
            content="This is a valid meta description under 155 characters."
        )
        assert len(meta.content) <= 155
    
    def test_meta_too_long(self):
        """Test that meta over 155 chars raises error."""
        with pytest.raises(ValidationError):
            MetaDescriptionSection(content="A" * 156)


class TestKeyFeaturesSection:
    """Tests for KeyFeaturesSection."""
    
    def test_valid_features(self):
        """Test valid key features."""
        features = KeyFeaturesSection(features=[
            "Feature 1",
            "Feature 2",
            "Feature 3",
        ])
        assert len(features.features) == 3
    
    def test_too_few_features(self):
        """Test that fewer than 3 features raises error."""
        with pytest.raises(ValidationError):
            KeyFeaturesSection(features=["Feature 1", "Feature 2"])
    
    def test_too_many_features(self):
        """Test that more than 5 features raises error."""
        with pytest.raises(ValidationError):
            KeyFeaturesSection(features=[f"Feature {i}" for i in range(6)])
    
    def test_to_html(self):
        """Test HTML generation."""
        features = KeyFeaturesSection(features=["A", "B", "C"])
        html = features.to_html()
        
        assert '<ul id="key-features">' in html
        assert "<li>A</li>" in html
        assert "<li>B</li>" in html
        assert "<li>C</li>" in html

