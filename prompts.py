"""Prompt templates for content generation."""

from typing import Any
from ..models.property import PropertyInput, Language, Tone, Region, ListingType


class PromptBuilder:
    """
    Builder for constructing LLM prompts for real estate content generation.
    
    Design Decision:
    - Separated prompt building from generation for testability and maintainability
    - Language-specific templates ensure natural output in each language
    - Tone modifiers adjust vocabulary and style without changing structure
    - Regional SEO keywords are injected based on target market
    """
    
    # Language-specific system prompts
    LANGUAGE_CONFIGS = {
        Language.ENGLISH: {
            "name": "English",
            "listing_words": {"sale": "for Sale", "rent": "for Rent"},
            "seo_phrases": [
                "property for {listing_type}",
                "real estate in {city}",
                "{property_type} in {neighborhood}",
                "buy property in {city}",
            ],
        },
        Language.PORTUGUESE: {
            "name": "Portuguese",
            "listing_words": {"sale": "à Venda", "rent": "para Arrendar"},
            "seo_phrases": [
                "imóvel para {listing_type}",
                "imobiliário em {city}",
                "{property_type} em {neighborhood}",
                "comprar casa em {city}",
            ],
        },
        Language.SPANISH: {
            "name": "Spanish",
            "listing_words": {"sale": "en Venta", "rent": "en Alquiler"},
            "seo_phrases": [
                "propiedad en {listing_type}",
                "inmuebles en {city}",
                "{property_type} en {neighborhood}",
                "comprar piso en {city}",
            ],
        },
        Language.FRENCH: {
            "name": "French",
            "listing_words": {"sale": "à Vendre", "rent": "à Louer"},
            "seo_phrases": [
                "propriété {listing_type}",
                "immobilier à {city}",
                "{property_type} à {neighborhood}",
                "acheter appartement à {city}",
            ],
        },
        Language.ITALIAN: {
            "name": "Italian",
            "listing_words": {"sale": "in Vendita", "rent": "in Affitto"},
            "seo_phrases": [
                "proprietà {listing_type}",
                "immobili a {city}",
                "{property_type} a {neighborhood}",
                "comprare casa a {city}",
            ],
        },
    }
    
    # Tone-specific modifiers
    TONE_CONFIGS = {
        Tone.FORMAL: {
            "style": "professional, sophisticated, and precise",
            "vocabulary": "formal business language with technical property terms",
            "avoid": "casual expressions, exclamations, or overly enthusiastic language",
        },
        Tone.FRIENDLY: {
            "style": "warm, welcoming, and approachable",
            "vocabulary": "conversational yet informative language",
            "avoid": "stiff or overly technical language",
        },
        Tone.LUXURY: {
            "style": "elegant, exclusive, and aspirational",
            "vocabulary": "premium, upscale descriptors emphasizing quality and prestige",
            "avoid": "budget-focused language, casual expressions",
        },
        Tone.INVESTOR: {
            "style": "analytical, ROI-focused, and data-driven",
            "vocabulary": "investment terms, yield potential, market positioning",
            "avoid": "emotional appeals, lifestyle-focused descriptions",
        },
    }
    
    # Regional SEO variations
    REGIONAL_SEO = {
        Region.UK: {
            "area_unit": "sq ft",
            "conversion": 10.764,  # sqm to sqft
            "keywords": ["flat", "property", "estate agent"],
        },
        Region.US: {
            "area_unit": "sq ft",
            "conversion": 10.764,
            "keywords": ["apartment", "condo", "realtor", "real estate"],
        },
        Region.PORTUGAL: {
            "area_unit": "m²",
            "conversion": 1,
            "keywords": ["apartamento", "imóvel", "imobiliária"],
        },
        Region.BRAZIL: {
            "area_unit": "m²",
            "conversion": 1,
            "keywords": ["apartamento", "imóvel", "corretor"],
        },
        Region.DEFAULT: {
            "area_unit": "sqm",
            "conversion": 1,
            "keywords": [],
        },
    }
    
    def __init__(self, property_data: PropertyInput):
        """Initialize prompt builder with property data."""
        self.property = property_data
        self.lang_config = self.LANGUAGE_CONFIGS[property_data.language]
        self.tone_config = self.TONE_CONFIGS[property_data.tone]
        self.region_config = self.REGIONAL_SEO.get(
            property_data.region_seo, 
            self.REGIONAL_SEO[Region.DEFAULT]
        )
    
    def build_system_prompt(self) -> str:
        """
        Build the system prompt that sets the AI's role and constraints.
        
        Returns:
            System prompt string for the LLM.
        """
        language_name = self.lang_config["name"]
        tone_style = self.tone_config["style"]
        tone_vocab = self.tone_config["vocabulary"]
        tone_avoid = self.tone_config["avoid"]
        
        return f"""You are an expert real estate copywriter specializing in SEO-optimized property listings.

LANGUAGE: Generate ALL content in {language_name}. Do not mix languages.

TONE: Write in a {tone_style} style using {tone_vocab}. Avoid {tone_avoid}.

SEO REQUIREMENTS:
- Include relevant location-based keywords naturally
- Use property type and city combinations
- Include calls to action
- Do NOT keyword stuff or use repetitive language
- Do NOT include misleading information

CONTENT STRUCTURE REQUIREMENTS:
You must generate content for exactly 7 sections with specific constraints:

1. PAGE TITLE: Max 60 characters. Include property type, listing type, and location.

2. META DESCRIPTION: Max 155 characters. Compelling summary with key features and location.

3. HEADLINE (H1): Engaging, descriptive headline highlighting key property features.

4. FULL DESCRIPTION: 500-700 characters. Rich, engaging paragraph covering:
   - Property location and neighborhood appeal
   - Size and layout
   - Key features and amenities
   - Building characteristics (floor, elevator, year built)
   - Price and value proposition

5. KEY FEATURES: Exactly 3-5 bullet points with most important features.

6. NEIGHBORHOOD SUMMARY: One paragraph about the area, lifestyle, and conveniences.

7. CALL TO ACTION: Short, compelling closing line encouraging user action.

OUTPUT FORMAT:
Respond with a valid JSON object containing these exact keys:
- title (string, max 60 chars)
- meta_description (string, max 155 chars)  
- headline (string)
- description (string, 500-700 chars)
- key_features (array of 3-5 strings)
- neighborhood (string)
- call_to_action (string)

IMPORTANT: Ensure all character limits are strictly followed. Count characters carefully."""

    def build_user_prompt(self) -> str:
        """
        Build the user prompt with property-specific details.
        
        Returns:
            User prompt string with all property information.
        """
        p = self.property
        f = p.features
        
        # Format listing type for the target language
        listing_word = self.lang_config["listing_words"].get(
            p.listing_type.value, 
            p.listing_type.value
        )
        
        # Calculate area in regional units
        area_value = f.area_sqm * self.region_config["conversion"]
        area_unit = self.region_config["area_unit"]
        
        # Build feature list
        features_list = []
        features_list.append(f"- Bedrooms: {f.bedrooms}")
        features_list.append(f"- Bathrooms: {f.bathrooms}")
        features_list.append(f"- Area: {area_value:.0f} {area_unit}")
        
        if f.floor is not None:
            features_list.append(f"- Floor: {f.floor}")
        if f.year_built:
            features_list.append(f"- Year built: {f.year_built}")
        
        # Boolean features
        bool_features = {
            "balcony": "Balcony",
            "parking": "Parking",
            "elevator": "Elevator",
            "garden": "Garden",
            "pool": "Swimming pool",
            "terrace": "Terrace",
            "storage": "Storage room",
            "air_conditioning": "Air conditioning",
            "heating": "Central heating",
            "furnished": "Furnished",
            "renovated": "Recently renovated",
        }
        
        for attr, label in bool_features.items():
            if getattr(f, attr, False):
                features_list.append(f"- {label}: Yes")
        
        if f.energy_rating:
            features_list.append(f"- Energy rating: {f.energy_rating}")
        
        features_str = "\n".join(features_list)
        
        # Build neighborhood context
        neighborhood_str = p.location.neighborhood or p.location.city
        
        # Build complete prompt
        prompt = f"""Generate SEO-optimized real estate listing content for this property:

PROPERTY DETAILS:
- Title: {p.title}
- Type: {p.get_property_type()}
- Listing: {listing_word}
- Price: {p.format_price()}

LOCATION:
- City: {p.location.city}
- Neighborhood: {neighborhood_str}
{f'- Region: {p.location.region}' if p.location.region else ''}
{f'- Country: {p.location.country}' if p.location.country else ''}

FEATURES:
{features_str}
"""
        
        # Add extra description if provided
        if p.description_extra:
            prompt += f"\nADDITIONAL DETAILS:\n{p.description_extra}\n"
        
        # Add highlights if provided
        if p.highlights:
            highlights_str = "\n".join(f"- {h}" for h in p.highlights)
            prompt += f"\nHIGHLIGHTS TO EMPHASIZE:\n{highlights_str}\n"
        
        prompt += "\nGenerate the content now, ensuring all character limits are met."
        
        return prompt
    
    def get_seo_keywords(self) -> list[str]:
        """
        Get relevant SEO keywords for validation.
        
        Returns:
            List of SEO keywords to check in generated content.
        """
        p = self.property
        keywords = []
        
        # Language-specific SEO phrases
        for phrase_template in self.lang_config["seo_phrases"]:
            listing_word = self.lang_config["listing_words"].get(
                p.listing_type.value,
                p.listing_type.value
            )
            keyword = phrase_template.format(
                listing_type=listing_word,
                city=p.location.city,
                neighborhood=p.location.neighborhood or p.location.city,
                property_type=p.get_property_type(),
            )
            keywords.append(keyword.lower())
        
        # Regional keywords
        keywords.extend(self.region_config.get("keywords", []))
        
        # Essential terms
        keywords.append(p.location.city.lower())
        if p.location.neighborhood:
            keywords.append(p.location.neighborhood.lower())
        
        return keywords


def get_json_schema() -> dict[str, Any]:
    """
    Get JSON schema for structured output from OpenAI.
    
    Returns:
        JSON schema dictionary for response format.
    """
    return {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Page title, max 60 characters"
            },
            "meta_description": {
                "type": "string", 
                "description": "Meta description, max 155 characters"
            },
            "headline": {
                "type": "string",
                "description": "Main H1 headline"
            },
            "description": {
                "type": "string",
                "description": "Full property description, 500-700 characters"
            },
            "key_features": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 3,
                "maxItems": 5,
                "description": "3-5 key feature bullet points"
            },
            "neighborhood": {
                "type": "string",
                "description": "Neighborhood summary paragraph"
            },
            "call_to_action": {
                "type": "string",
                "description": "Call to action closing line"
            }
        },
        "required": [
            "title",
            "meta_description", 
            "headline",
            "description",
            "key_features",
            "neighborhood",
            "call_to_action"
        ],
        "additionalProperties": False
    }

