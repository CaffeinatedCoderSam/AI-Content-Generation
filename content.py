"""Content output models with HTML formatting."""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ContentSection(BaseModel):
    """Base model for a content section."""
    content: str = Field(..., min_length=1)
    

class TitleSection(ContentSection):
    """Page title section (max 60 characters)."""
    
    @field_validator('content')
    @classmethod
    def validate_length(cls, v: str) -> str:
        if len(v) > 60:
            raise ValueError(f"Title must be max 60 characters, got {len(v)}")
        return v
    
    def to_html(self) -> str:
        """Generate HTML title tag."""
        return f"<title>{self.content}</title>"


class MetaDescriptionSection(ContentSection):
    """Meta description section (max 155 characters)."""
    
    @field_validator('content')
    @classmethod
    def validate_length(cls, v: str) -> str:
        if len(v) > 155:
            raise ValueError(f"Meta description must be max 155 characters, got {len(v)}")
        return v
    
    def to_html(self) -> str:
        """Generate HTML meta description tag."""
        return f'<meta name="description" content="{self.content}">'


class HeadlineSection(ContentSection):
    """H1 headline section."""
    
    def to_html(self) -> str:
        """Generate HTML h1 tag."""
        return f"<h1>{self.content}</h1>"


class DescriptionSection(ContentSection):
    """Full property description section (500-700 characters)."""
    
    @field_validator('content')
    @classmethod
    def validate_length(cls, v: str) -> str:
        if len(v) < 400:  # Allow some flexibility
            raise ValueError(f"Description should be at least 400 characters, got {len(v)}")
        if len(v) > 800:  # Allow some flexibility
            raise ValueError(f"Description should be max 800 characters, got {len(v)}")
        return v
    
    def to_html(self) -> str:
        """Generate HTML section with description."""
        return f'<section id="description">\n  <p>{self.content}</p>\n</section>'


class KeyFeaturesSection(BaseModel):
    """Key features list section (3-5 bullet points)."""
    features: list[str] = Field(..., min_length=3, max_length=5)
    
    def to_html(self) -> str:
        """Generate HTML unordered list."""
        items = "\n".join(f"  <li>{feature}</li>" for feature in self.features)
        return f'<ul id="key-features">\n{items}\n</ul>'


class NeighborhoodSection(ContentSection):
    """Neighborhood summary section."""
    
    def to_html(self) -> str:
        """Generate HTML section with neighborhood info."""
        return f'<section id="neighborhood">\n  <p>{self.content}</p>\n</section>'


class CallToActionSection(ContentSection):
    """Call to action closing section."""
    
    def to_html(self) -> str:
        """Generate HTML paragraph with CTA."""
        return f'<p class="call-to-action">{self.content}</p>'


class GeneratedContent(BaseModel):
    """
    Complete generated content for a property listing.
    
    Contains all HTML-tagged sections required for SEO-optimized
    real estate listing pages.
    """
    title: TitleSection = Field(..., description="Page title (max 60 chars)")
    meta_description: MetaDescriptionSection = Field(
        ..., 
        description="SEO meta description (max 155 chars)"
    )
    headline: HeadlineSection = Field(..., description="Main H1 headline")
    description: DescriptionSection = Field(
        ..., 
        description="Full property description (500-700 chars)"
    )
    key_features: KeyFeaturesSection = Field(
        ..., 
        description="3-5 key feature bullet points"
    )
    neighborhood: NeighborhoodSection = Field(
        ..., 
        description="Neighborhood summary paragraph"
    )
    call_to_action: CallToActionSection = Field(..., description="CTA closing line")
    
    # Metadata
    language: str = Field(..., description="Content language code")
    tone: str = Field(..., description="Content tone used")
    
    def to_html(self) -> str:
        """
        Generate complete HTML output with all sections.
        
        Returns formatted HTML string with proper spacing between sections.
        """
        sections = [
            self.title.to_html(),
            "",
            self.meta_description.to_html(),
            "",
            self.headline.to_html(),
            "",
            self.description.to_html(),
            "",
            self.key_features.to_html(),
            "",
            self.neighborhood.to_html(),
            "",
            self.call_to_action.to_html(),
        ]
        return "\n".join(sections)
    
    def to_dict(self) -> dict:
        """Return content as dictionary with HTML strings."""
        return {
            "title": self.title.to_html(),
            "meta_description": self.meta_description.to_html(),
            "headline": self.headline.to_html(),
            "description": self.description.to_html(),
            "key_features": self.key_features.to_html(),
            "neighborhood": self.neighborhood.to_html(),
            "call_to_action": self.call_to_action.to_html(),
            "language": self.language,
            "tone": self.tone,
        }


class ContentValidationResult(BaseModel):
    """Result of content validation checks."""
    is_valid: bool = Field(..., description="Overall validation status")
    errors: list[str] = Field(default_factory=list, description="Validation errors")
    warnings: list[str] = Field(default_factory=list, description="Validation warnings")
    seo_score: Optional[float] = Field(None, ge=0, le=100, description="SEO score (0-100)")
    readability_score: Optional[float] = Field(
        None, 
        ge=0, 
        le=100, 
        description="Readability score (0-100)"
    )
    
    def add_error(self, error: str) -> None:
        """Add a validation error."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str) -> None:
        """Add a validation warning."""
        self.warnings.append(warning)

