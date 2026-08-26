"""Property input data models with validation."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class Language(str, Enum):
    """Supported languages for content generation."""
    ENGLISH = "en"
    PORTUGUESE = "pt"
    SPANISH = "es"
    FRENCH = "fr"
    ITALIAN = "it"


class ListingType(str, Enum):
    """Type of property listing."""
    SALE = "sale"
    RENT = "rent"


class Tone(str, Enum):
    """Content tone options for customization."""
    FORMAL = "formal"
    FRIENDLY = "friendly"
    LUXURY = "luxury"
    INVESTOR = "investor"


class Region(str, Enum):
    """Regional SEO variations."""
    PORTUGAL = "pt"
    SPAIN = "es"
    FRANCE = "fr"
    ITALY = "it"
    UK = "uk"
    US = "us"
    BRAZIL = "br"
    DEFAULT = "default"


class Location(BaseModel):
    """Property location details."""
    city: str = Field(..., min_length=1, description="City name")
    neighborhood: Optional[str] = Field(None, description="Neighborhood or district")
    region: Optional[str] = Field(None, description="Region or state")
    country: Optional[str] = Field(None, description="Country")
    postal_code: Optional[str] = Field(None, description="Postal/ZIP code")


class Features(BaseModel):
    """Property features and specifications."""
    bedrooms: int = Field(..., ge=0, description="Number of bedrooms")
    bathrooms: int = Field(..., ge=0, description="Number of bathrooms")
    area_sqm: float = Field(..., gt=0, description="Total area in square meters")
    balcony: bool = Field(False, description="Has balcony")
    parking: bool = Field(False, description="Has parking")
    elevator: bool = Field(False, description="Building has elevator")
    floor: Optional[int] = Field(None, ge=0, description="Floor number")
    year_built: Optional[int] = Field(None, ge=1800, le=2100, description="Year built")
    garden: bool = Field(False, description="Has garden")
    pool: bool = Field(False, description="Has swimming pool")
    terrace: bool = Field(False, description="Has terrace")
    storage: bool = Field(False, description="Has storage room")
    air_conditioning: bool = Field(False, description="Has air conditioning")
    heating: bool = Field(False, description="Has central heating")
    furnished: bool = Field(False, description="Property is furnished")
    renovated: bool = Field(False, description="Recently renovated")
    energy_rating: Optional[str] = Field(None, description="Energy efficiency rating")
    
    @field_validator('energy_rating')
    @classmethod
    def validate_energy_rating(cls, v: Optional[str]) -> Optional[str]:
        """Validate energy rating format."""
        if v is not None:
            valid_ratings = ['A+', 'A', 'B', 'C', 'D', 'E', 'F', 'G']
            if v.upper() not in valid_ratings:
                raise ValueError(f"Energy rating must be one of: {valid_ratings}")
            return v.upper()
        return v


class PropertyInput(BaseModel):
    """
    Complete property input model for content generation.
    
    This model validates and structures all property data needed
    to generate SEO-optimized content for real estate listings.
    """
    title: str = Field(..., min_length=1, description="Property title")
    location: Location = Field(..., description="Property location")
    features: Features = Field(..., description="Property features")
    price: float = Field(..., gt=0, description="Property price")
    currency: str = Field("EUR", description="Price currency")
    listing_type: ListingType = Field(..., description="Sale or rent")
    language: Language = Field(Language.ENGLISH, description="Output language")
    tone: Tone = Field(Tone.FRIENDLY, description="Content tone")
    region_seo: Region = Field(Region.DEFAULT, description="Regional SEO optimization")
    
    # Optional additional details
    description_extra: Optional[str] = Field(
        None, 
        description="Additional details to include in description"
    )
    highlights: Optional[list[str]] = Field(
        None,
        description="Specific highlights to emphasize"
    )
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "title": "T3 apartment in Lisbon",
                "location": {
                    "city": "Lisbon",
                    "neighborhood": "Campo de Ourique"
                },
                "features": {
                    "bedrooms": 3,
                    "bathrooms": 2,
                    "area_sqm": 120,
                    "balcony": True,
                    "parking": False,
                    "elevator": True,
                    "floor": 2,
                    "year_built": 2005
                },
                "price": 650000,
                "listing_type": "sale",
                "language": "en",
                "tone": "friendly"
            }
        }
    
    def get_property_type(self) -> str:
        """
        Determine property type based on bedrooms.
        Returns localized property type string.
        """
        type_map = {
            Language.ENGLISH: {
                0: "Studio",
                1: "1-bedroom apartment",
                2: "2-bedroom apartment",
                3: "3-bedroom apartment",
                4: "4-bedroom apartment",
                5: "5-bedroom property",
            },
            Language.PORTUGUESE: {
                0: "Estúdio",
                1: "T1",
                2: "T2",
                3: "T3",
                4: "T4",
                5: "T5",
            },
            Language.SPANISH: {
                0: "Estudio",
                1: "Apartamento de 1 habitación",
                2: "Apartamento de 2 habitaciones",
                3: "Apartamento de 3 habitaciones",
                4: "Apartamento de 4 habitaciones",
                5: "Propiedad de 5 habitaciones",
            },
            Language.FRENCH: {
                0: "Studio",
                1: "Appartement 2 pièces",
                2: "Appartement 3 pièces",
                3: "Appartement 4 pièces",
                4: "Appartement 5 pièces",
                5: "Propriété 6 pièces",
            },
            Language.ITALIAN: {
                0: "Monolocale",
                1: "Bilocale",
                2: "Trilocale",
                3: "Quadrilocale",
                4: "Appartamento 5 locali",
                5: "Proprietà 6 locali",
            },
        }
        
        bedrooms = min(self.features.bedrooms, 5)
        return type_map.get(self.language, type_map[Language.ENGLISH]).get(
            bedrooms, 
            f"{bedrooms}+ bedroom property"
        )
    
    def format_price(self) -> str:
        """Format price with currency symbol."""
        currency_symbols = {
            "EUR": "€",
            "USD": "$",
            "GBP": "£",
            "BRL": "R$",
        }
        symbol = currency_symbols.get(self.currency, self.currency)
        
        # Format with thousands separator
        formatted = f"{self.price:,.0f}".replace(",", " ")
        
        if self.listing_type == ListingType.RENT:
            month_labels = {
                Language.ENGLISH: "/month",
                Language.PORTUGUESE: "/mês",
                Language.SPANISH: "/mes",
                Language.FRENCH: "/mois",
                Language.ITALIAN: "/mese",
            }
            return f"{symbol}{formatted}{month_labels.get(self.language, '/month')}"
        
        return f"{symbol}{formatted}"

