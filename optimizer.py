"""SEO optimization and validation for generated content."""

import re
from dataclasses import dataclass, field
from typing import Optional

from ..models.property import PropertyInput, Language
from ..models.content import GeneratedContent


@dataclass
class SEOAnalysis:
    """
    Comprehensive SEO analysis result.
    
    Provides detailed scoring and recommendations for improving
    search engine optimization of generated content.
    """
    overall_score: float = 0.0
    
    # Component scores (0-100)
    title_score: float = 0.0
    meta_description_score: float = 0.0
    headline_score: float = 0.0
    description_score: float = 0.0
    keyword_score: float = 0.0
    
    # Issues and recommendations
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    
    # Keyword analysis
    keywords_found: list[str] = field(default_factory=list)
    keywords_missing: list[str] = field(default_factory=list)
    keyword_density: float = 0.0
    
    def is_passing(self) -> bool:
        """Check if content passes minimum SEO requirements."""
        return self.overall_score >= 70 and len(self.issues) == 0
    
    def to_dict(self) -> dict:
        """Convert analysis to dictionary."""
        return {
            "overall_score": round(self.overall_score, 1),
            "component_scores": {
                "title": round(self.title_score, 1),
                "meta_description": round(self.meta_description_score, 1),
                "headline": round(self.headline_score, 1),
                "description": round(self.description_score, 1),
                "keywords": round(self.keyword_score, 1),
            },
            "is_passing": self.is_passing(),
            "issues": self.issues,
            "warnings": self.warnings,
            "recommendations": self.recommendations,
            "keyword_analysis": {
                "found": self.keywords_found,
                "missing": self.keywords_missing,
                "density": round(self.keyword_density, 2),
            },
        }


class SEOOptimizer:
    """
    SEO optimizer for real estate content.
    
    Design Principles:
    
    1. Language-Aware Analysis:
       - Different languages have different SEO patterns
       - Stop words and keyword variations are language-specific
    
    2. Real Estate Focus:
       - Optimized for property listing search patterns
       - Location + property type combinations
       - Price and feature keywords
    
    3. Non-Destructive:
       - Analysis provides recommendations
       - Does not automatically modify content
       - Allows human review before changes
    """
    
    # Language-specific stop words
    STOP_WORDS = {
        Language.ENGLISH: {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", 
            "for", "of", "with", "by", "is", "are", "was", "were", "be",
            "this", "that", "these", "those", "it", "its", "your", "our",
        },
        Language.PORTUGUESE: {
            "o", "a", "os", "as", "um", "uma", "uns", "umas", "e", "ou",
            "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
            "para", "por", "com", "sem", "é", "são", "está", "estão",
        },
        Language.SPANISH: {
            "el", "la", "los", "las", "un", "una", "unos", "unas", "y", "o",
            "de", "del", "en", "con", "por", "para", "es", "son", "está",
            "están", "este", "esta", "estos", "estas", "ese", "esa",
        },
        Language.FRENCH: {
            "le", "la", "les", "un", "une", "des", "et", "ou", "de", "du",
            "en", "dans", "sur", "avec", "pour", "par", "est", "sont",
            "ce", "cette", "ces", "il", "elle", "ils", "elles",
        },
        Language.ITALIAN: {
            "il", "lo", "la", "i", "gli", "le", "un", "uno", "una", "e",
            "o", "di", "del", "della", "in", "nel", "nella", "con", "per",
            "è", "sono", "questo", "questa", "questi", "queste",
        },
    }
    
    # SEO keyword patterns by language
    KEYWORD_PATTERNS = {
        Language.ENGLISH: [
            r"(apartment|flat|house|property|home)\s+(for\s+)?(sale|rent)",
            r"(bedroom|bathroom|sqm|square\s+meter)",
            r"(real\s+estate|buy|purchase|invest)",
        ],
        Language.PORTUGUESE: [
            r"(apartamento|casa|imóvel|moradia)\s+(à\s+)?(venda|arrendar)",
            r"(quarto|casa\s+de\s+banho|m²)",
            r"(imobiliário|comprar|investir)",
        ],
        Language.SPANISH: [
            r"(apartamento|piso|casa|propiedad)\s+(en\s+)?(venta|alquiler)",
            r"(habitación|dormitorio|baño|m²)",
            r"(inmobiliaria|comprar|invertir)",
        ],
        Language.FRENCH: [
            r"(appartement|maison|propriété)\s+(à\s+)?(vendre|louer)",
            r"(chambre|salle\s+de\s+bain|m²)",
            r"(immobilier|acheter|investir)",
        ],
        Language.ITALIAN: [
            r"(appartamento|casa|proprietà)\s+(in\s+)?(vendita|affitto)",
            r"(camera|bagno|mq)",
            r"(immobiliare|comprare|investire)",
        ],
    }
    
    # Call to action patterns
    CTA_PATTERNS = {
        Language.ENGLISH: [
            r"schedule.*(visit|viewing|tour)",
            r"contact\s+us",
            r"don't\s+miss",
            r"call\s+(today|now)",
            r"book\s+a\s+(viewing|tour)",
        ],
        Language.PORTUGUESE: [
            r"agende.*(visita|visitar)",
            r"entre\s+em\s+contato",
            r"não\s+perca",
            r"ligue\s+(hoje|agora)",
            r"marque\s+uma\s+visita",
        ],
        Language.SPANISH: [
            r"programe.*(visita)",
            r"contáct(e|a)nos",
            r"no\s+pierda",
            r"llame\s+(hoy|ahora)",
            r"reserve\s+una\s+visita",
        ],
        Language.FRENCH: [
            r"planifi(er|ez).*(visite)",
            r"contactez(-|\s+)nous",
            r"ne\s+manquez\s+pas",
            r"appel(er|ez)\s+(aujourd'hui|maintenant)",
            r"réserv(er|ez)\s+une\s+visite",
        ],
        Language.ITALIAN: [
            r"prenot(a|i).*(visita)",
            r"contattaci",
            r"non\s+perd(ere|a)",
            r"chiam(a|i)\s+(oggi|adesso)",
            r"prenota\s+una\s+visita",
        ],
    }
    
    def __init__(self, property_data: PropertyInput):
        """
        Initialize SEO optimizer with property context.
        
        Args:
            property_data: Property input for context-aware analysis
        """
        self.property = property_data
        self.language = property_data.language
        self.stop_words = self.STOP_WORDS.get(
            self.language, 
            self.STOP_WORDS[Language.ENGLISH]
        )
    
    def analyze(self, content: GeneratedContent) -> SEOAnalysis:
        """
        Perform comprehensive SEO analysis on generated content.
        
        Args:
            content: Generated content to analyze
            
        Returns:
            SEOAnalysis with scores and recommendations
        """
        analysis = SEOAnalysis()
        
        # Analyze each component
        analysis.title_score = self._analyze_title(content.title.content, analysis)
        analysis.meta_description_score = self._analyze_meta_description(
            content.meta_description.content, analysis
        )
        analysis.headline_score = self._analyze_headline(content.headline.content, analysis)
        analysis.description_score = self._analyze_description(
            content.description.content, analysis
        )
        analysis.keyword_score = self._analyze_keywords(content, analysis)
        
        # Calculate overall score (weighted average)
        weights = {
            "title": 0.20,
            "meta_description": 0.20,
            "headline": 0.15,
            "description": 0.25,
            "keywords": 0.20,
        }
        
        analysis.overall_score = (
            analysis.title_score * weights["title"] +
            analysis.meta_description_score * weights["meta_description"] +
            analysis.headline_score * weights["headline"] +
            analysis.description_score * weights["description"] +
            analysis.keyword_score * weights["keywords"]
        )
        
        # Add general recommendations
        if analysis.overall_score < 80:
            analysis.recommendations.append(
                "Consider adding more location-specific keywords"
            )
        
        return analysis
    
    def _analyze_title(self, title: str, analysis: SEOAnalysis) -> float:
        """Analyze title for SEO effectiveness."""
        score = 100.0
        
        # Length check (optimal: 50-60 chars)
        length = len(title)
        if length < 30:
            score -= 20
            analysis.warnings.append(f"Title too short ({length} chars, optimal: 50-60)")
        elif length > 60:
            score -= 30
            analysis.issues.append(f"Title exceeds 60 characters ({length})")
        
        # Location inclusion
        city = self.property.location.city.lower()
        if city not in title.lower():
            score -= 15
            analysis.recommendations.append("Include city name in title")
        else:
            analysis.keywords_found.append(city)
        
        # Neighborhood inclusion (if available)
        neighborhood = self.property.location.neighborhood
        if neighborhood and neighborhood.lower() in title.lower():
            score += 5  # Bonus for neighborhood
            analysis.keywords_found.append(neighborhood.lower())
        
        # Listing type check
        listing_keywords = {
            Language.ENGLISH: ["sale", "rent", "for sale", "for rent"],
            Language.PORTUGUESE: ["venda", "arrendar", "à venda"],
            Language.SPANISH: ["venta", "alquiler", "en venta"],
            Language.FRENCH: ["vendre", "louer", "à vendre"],
            Language.ITALIAN: ["vendita", "affitto", "in vendita"],
        }
        
        keywords = listing_keywords.get(self.language, listing_keywords[Language.ENGLISH])
        if not any(kw in title.lower() for kw in keywords):
            score -= 10
            analysis.recommendations.append("Include listing type (sale/rent) in title")
        
        return max(0, min(100, score))
    
    def _analyze_meta_description(self, meta: str, analysis: SEOAnalysis) -> float:
        """Analyze meta description for SEO effectiveness."""
        score = 100.0
        
        # Length check (optimal: 120-155 chars)
        length = len(meta)
        if length < 100:
            score -= 20
            analysis.warnings.append(f"Meta description short ({length} chars, optimal: 120-155)")
        elif length > 155:
            score -= 30
            analysis.issues.append(f"Meta description exceeds 155 characters ({length})")
        
        # Location inclusion
        city = self.property.location.city.lower()
        if city not in meta.lower():
            score -= 15
            analysis.recommendations.append("Include city in meta description")
        
        # Feature mentions
        feature_words = ["bedroom", "bathroom", "sqm", "m²", "balcony", "parking"]
        feature_count = sum(1 for w in feature_words if w in meta.lower())
        if feature_count < 2:
            score -= 10
            analysis.recommendations.append("Mention key features in meta description")
        
        # Call to action presence
        cta_patterns = self.CTA_PATTERNS.get(
            self.language, 
            self.CTA_PATTERNS[Language.ENGLISH]
        )
        has_cta = any(re.search(p, meta.lower()) for p in cta_patterns)
        if not has_cta:
            score -= 5
            analysis.recommendations.append("Consider adding CTA to meta description")
        
        return max(0, min(100, score))
    
    def _analyze_headline(self, headline: str, analysis: SEOAnalysis) -> float:
        """Analyze H1 headline for SEO effectiveness."""
        score = 100.0
        
        # Length check
        length = len(headline)
        if length < 20:
            score -= 15
            analysis.warnings.append("Headline too short")
        elif length > 100:
            score -= 10
            analysis.warnings.append("Headline may be too long for display")
        
        # Location inclusion
        city = self.property.location.city.lower()
        neighborhood = self.property.location.neighborhood
        
        has_location = city in headline.lower()
        if neighborhood:
            has_location = has_location or neighborhood.lower() in headline.lower()
        
        if not has_location:
            score -= 20
            analysis.recommendations.append("Include location in headline")
        
        # Keyword patterns
        patterns = self.KEYWORD_PATTERNS.get(
            self.language,
            self.KEYWORD_PATTERNS[Language.ENGLISH]
        )
        
        pattern_matches = sum(
            1 for p in patterns if re.search(p, headline.lower())
        )
        if pattern_matches == 0:
            score -= 15
            analysis.recommendations.append("Include property type keywords in headline")
        
        return max(0, min(100, score))
    
    def _analyze_description(self, description: str, analysis: SEOAnalysis) -> float:
        """Analyze main description for SEO effectiveness."""
        score = 100.0
        
        # Length check (optimal: 500-700 chars)
        length = len(description)
        if length < 400:
            score -= 20
            analysis.issues.append(f"Description too short ({length} chars)")
        elif length > 800:
            score -= 15
            analysis.warnings.append(f"Description may be too long ({length} chars)")
        
        # Keyword density
        words = description.lower().split()
        total_words = len(words)
        
        # Count location mentions
        city = self.property.location.city.lower()
        neighborhood = self.property.location.neighborhood
        
        city_count = description.lower().count(city)
        if city_count == 0:
            score -= 15
            analysis.issues.append("City not mentioned in description")
        elif city_count > 5:
            score -= 10
            analysis.warnings.append("Possible keyword stuffing (city mentioned too often)")
        
        # Feature coverage
        features_mentioned = 0
        feature_terms = {
            "bedrooms": str(self.property.features.bedrooms),
            "bathrooms": str(self.property.features.bathrooms),
            "area": str(int(self.property.features.area_sqm)),
        }
        
        for feature, value in feature_terms.items():
            if value in description:
                features_mentioned += 1
        
        if features_mentioned < 2:
            score -= 10
            analysis.recommendations.append("Include more specific property features")
        
        # Price mention
        if self.property.format_price().replace(" ", "") not in description.replace(" ", ""):
            # Check if price is mentioned in any format
            price_str = str(int(self.property.price))
            if price_str not in description.replace(",", "").replace(".", ""):
                score -= 5
                analysis.recommendations.append("Consider mentioning the price")
        
        # Readability (simple check - sentence length)
        sentences = re.split(r'[.!?]+', description)
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        
        if avg_sentence_length > 30:
            score -= 10
            analysis.warnings.append("Consider shorter sentences for readability")
        
        return max(0, min(100, score))
    
    def _analyze_keywords(self, content: GeneratedContent, analysis: SEOAnalysis) -> float:
        """Analyze overall keyword usage and density."""
        score = 100.0
        
        # Combine all text content
        full_text = " ".join([
            content.title.content,
            content.meta_description.content,
            content.headline.content,
            content.description.content,
            " ".join(content.key_features.features),
            content.neighborhood.content,
            content.call_to_action.content,
        ]).lower()
        
        # Required keywords
        required_keywords = [
            self.property.location.city.lower(),
        ]
        
        if self.property.location.neighborhood:
            required_keywords.append(self.property.location.neighborhood.lower())
        
        # Check required keywords
        for keyword in required_keywords:
            if keyword in full_text:
                analysis.keywords_found.append(keyword)
            else:
                analysis.keywords_missing.append(keyword)
                score -= 15
        
        # Check SEO patterns
        patterns = self.KEYWORD_PATTERNS.get(
            self.language,
            self.KEYWORD_PATTERNS[Language.ENGLISH]
        )
        
        pattern_matches = sum(1 for p in patterns if re.search(p, full_text))
        if pattern_matches < 2:
            score -= 10
            analysis.recommendations.append("Include more real estate keywords")
        
        # Calculate keyword density
        words = full_text.split()
        total_words = len(words)
        keyword_words = [w for w in words if w not in self.stop_words and len(w) > 3]
        
        # Count location keyword occurrences
        location_count = sum(
            full_text.count(kw) for kw in required_keywords
        )
        
        if total_words > 0:
            analysis.keyword_density = (location_count / total_words) * 100
            
            # Optimal density: 1-3%
            if analysis.keyword_density < 1:
                analysis.warnings.append("Keyword density may be too low")
            elif analysis.keyword_density > 5:
                score -= 15
                analysis.issues.append("Keyword density too high (possible stuffing)")
        
        # CTA presence check
        cta_patterns = self.CTA_PATTERNS.get(
            self.language,
            self.CTA_PATTERNS[Language.ENGLISH]
        )
        
        cta_text = content.call_to_action.content.lower()
        has_cta = any(re.search(p, cta_text) for p in cta_patterns)
        
        if not has_cta:
            score -= 10
            analysis.recommendations.append("Strengthen call-to-action with action verbs")
        
        return max(0, min(100, score))
    
    def get_suggestions(self, content: GeneratedContent) -> list[str]:
        """
        Get actionable suggestions for improving SEO.
        
        Args:
            content: Generated content to analyze
            
        Returns:
            List of improvement suggestions
        """
        analysis = self.analyze(content)
        suggestions = []
        
        suggestions.extend(analysis.issues)
        suggestions.extend(analysis.warnings)
        suggestions.extend(analysis.recommendations)
        
        # Add specific suggestions based on score
        if analysis.title_score < 80:
            suggestions.append(
                f"Improve title: Include '{self.property.location.city}' "
                f"and listing type"
            )
        
        if analysis.keyword_score < 70:
            suggestions.append(
                "Add more location and property type keywords naturally"
            )
        
        return suggestions

