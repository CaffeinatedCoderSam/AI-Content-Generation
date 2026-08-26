"""Content quality evaluation and scoring framework."""

import re
from dataclasses import dataclass, field
from typing import Optional

from ..models.property import PropertyInput, Language
from ..models.content import GeneratedContent
from ..seo.optimizer import SEOOptimizer, SEOAnalysis


@dataclass
class EvaluationReport:
    """
    Comprehensive evaluation report for generated content.
    
    Combines multiple quality dimensions:
    - Structure compliance
    - SEO effectiveness
    - Language fluency
    - Readability
    - Guideline compliance
    """
    # Overall scores
    overall_score: float = 0.0
    is_compliant: bool = True
    
    # Component scores (0-100)
    structure_score: float = 0.0
    seo_score: float = 0.0
    readability_score: float = 0.0
    fluency_score: float = 0.0
    
    # SEO analysis
    seo_analysis: Optional[SEOAnalysis] = None
    
    # Issues and feedback
    critical_issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    
    # Metadata
    language: str = ""
    tone: str = ""
    evaluation_details: dict = field(default_factory=dict)
    
    def add_critical_issue(self, issue: str) -> None:
        """Add a critical issue that fails compliance."""
        self.critical_issues.append(issue)
        self.is_compliant = False
    
    def to_dict(self) -> dict:
        """Convert report to dictionary format."""
        return {
            "overall_score": round(self.overall_score, 1),
            "is_compliant": self.is_compliant,
            "scores": {
                "structure": round(self.structure_score, 1),
                "seo": round(self.seo_score, 1),
                "readability": round(self.readability_score, 1),
                "fluency": round(self.fluency_score, 1),
            },
            "seo_details": self.seo_analysis.to_dict() if self.seo_analysis else None,
            "critical_issues": self.critical_issues,
            "warnings": self.warnings,
            "suggestions": self.suggestions,
            "metadata": {
                "language": self.language,
                "tone": self.tone,
            },
            "details": self.evaluation_details,
        }


class ContentEvaluator:
    """
    Comprehensive content quality evaluator.
    
    Design Philosophy:
    
    1. Multi-Dimensional Assessment:
       - Structure: HTML tags, section presence, length constraints
       - SEO: Keyword usage, meta optimization, search visibility
       - Readability: Sentence structure, complexity, clarity
       - Fluency: Grammar indicators, language naturalness
    
    2. Actionable Feedback:
       - Critical issues must be fixed
       - Warnings indicate potential problems
       - Suggestions provide optimization opportunities
    
    3. Language-Aware:
       - Readability metrics adapted per language
       - Fluency checks consider language patterns
    """
    
    # Character limit requirements
    LIMITS = {
        "title_max": 60,
        "meta_description_max": 155,
        "description_min": 400,
        "description_max": 800,
        "key_features_min": 3,
        "key_features_max": 5,
    }
    
    # Readability benchmarks by language (avg words per sentence)
    READABILITY_TARGETS = {
        Language.ENGLISH: {"optimal": 15, "max": 25},
        Language.PORTUGUESE: {"optimal": 18, "max": 28},
        Language.SPANISH: {"optimal": 17, "max": 27},
        Language.FRENCH: {"optimal": 18, "max": 28},
        Language.ITALIAN: {"optimal": 17, "max": 27},
    }
    
    def __init__(self, property_data: PropertyInput):
        """
        Initialize evaluator with property context.
        
        Args:
            property_data: Property input for context-aware evaluation
        """
        self.property = property_data
        self.language = property_data.language
        self.seo_optimizer = SEOOptimizer(property_data)
    
    def evaluate(self, content: GeneratedContent) -> EvaluationReport:
        """
        Perform comprehensive evaluation of generated content.
        
        Args:
            content: Generated content to evaluate
            
        Returns:
            EvaluationReport with scores and feedback
        """
        report = EvaluationReport(
            language=content.language,
            tone=content.tone,
        )
        
        # Evaluate each dimension
        report.structure_score = self._evaluate_structure(content, report)
        report.seo_analysis = self.seo_optimizer.analyze(content)
        report.seo_score = report.seo_analysis.overall_score
        report.readability_score = self._evaluate_readability(content, report)
        report.fluency_score = self._evaluate_fluency(content, report)
        
        # Calculate overall score (weighted average)
        weights = {
            "structure": 0.30,
            "seo": 0.30,
            "readability": 0.20,
            "fluency": 0.20,
        }
        
        report.overall_score = (
            report.structure_score * weights["structure"] +
            report.seo_score * weights["seo"] +
            report.readability_score * weights["readability"] +
            report.fluency_score * weights["fluency"]
        )
        
        # Add SEO suggestions
        report.suggestions.extend(report.seo_analysis.recommendations)
        
        return report
    
    def _evaluate_structure(
        self, 
        content: GeneratedContent, 
        report: EvaluationReport,
    ) -> float:
        """
        Evaluate structural compliance.
        
        Checks:
        - All required sections present
        - Character limits respected
        - HTML structure correct
        """
        score = 100.0
        details = {}
        
        # Title length
        title_len = len(content.title.content)
        details["title_length"] = title_len
        if title_len > self.LIMITS["title_max"]:
            score -= 20
            report.add_critical_issue(
                f"Title exceeds {self.LIMITS['title_max']} characters ({title_len})"
            )
        elif title_len < 20:
            score -= 10
            report.warnings.append(f"Title may be too short ({title_len} chars)")
        
        # Meta description length
        meta_len = len(content.meta_description.content)
        details["meta_description_length"] = meta_len
        if meta_len > self.LIMITS["meta_description_max"]:
            score -= 20
            report.add_critical_issue(
                f"Meta description exceeds {self.LIMITS['meta_description_max']} "
                f"characters ({meta_len})"
            )
        elif meta_len < 100:
            score -= 10
            report.warnings.append(
                f"Meta description may be too short ({meta_len} chars)"
            )
        
        # Description length
        desc_len = len(content.description.content)
        details["description_length"] = desc_len
        if desc_len < self.LIMITS["description_min"]:
            score -= 15
            report.add_critical_issue(
                f"Description below minimum ({desc_len} chars, "
                f"min: {self.LIMITS['description_min']})"
            )
        elif desc_len > self.LIMITS["description_max"]:
            score -= 10
            report.warnings.append(
                f"Description exceeds recommended length ({desc_len} chars)"
            )
        
        # Key features count
        features_count = len(content.key_features.features)
        details["key_features_count"] = features_count
        if features_count < self.LIMITS["key_features_min"]:
            score -= 15
            report.add_critical_issue(
                f"Too few key features ({features_count}, "
                f"min: {self.LIMITS['key_features_min']})"
            )
        elif features_count > self.LIMITS["key_features_max"]:
            score -= 5
            report.warnings.append(
                f"Too many key features ({features_count}, "
                f"max: {self.LIMITS['key_features_max']})"
            )
        
        # Headline presence and content
        if not content.headline.content.strip():
            score -= 20
            report.add_critical_issue("Headline is empty")
        
        # Neighborhood section
        if len(content.neighborhood.content) < 50:
            score -= 10
            report.warnings.append("Neighborhood section may be too short")
        
        # Call to action
        if len(content.call_to_action.content) < 20:
            score -= 10
            report.warnings.append("Call to action may be too short")
        
        report.evaluation_details["structure"] = details
        return max(0, score)
    
    def _evaluate_readability(
        self, 
        content: GeneratedContent, 
        report: EvaluationReport,
    ) -> float:
        """
        Evaluate content readability.
        
        Checks:
        - Sentence length
        - Paragraph structure
        - Word complexity
        """
        score = 100.0
        details = {}
        
        # Combine main text sections
        full_text = " ".join([
            content.description.content,
            content.neighborhood.content,
        ])
        
        # Sentence analysis
        sentences = re.split(r'[.!?]+', full_text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if sentences:
            word_counts = [len(s.split()) for s in sentences]
            avg_words = sum(word_counts) / len(sentences)
            max_words = max(word_counts)
            
            details["sentence_count"] = len(sentences)
            details["avg_words_per_sentence"] = round(avg_words, 1)
            details["max_words_in_sentence"] = max_words
            
            # Get language-specific targets
            targets = self.READABILITY_TARGETS.get(
                self.language,
                self.READABILITY_TARGETS[Language.ENGLISH]
            )
            
            if avg_words > targets["max"]:
                score -= 20
                report.warnings.append(
                    f"Sentences too long (avg: {avg_words:.1f} words, "
                    f"target: {targets['optimal']})"
                )
            elif avg_words > targets["optimal"] + 5:
                score -= 10
                report.suggestions.append(
                    "Consider shortening some sentences for better readability"
                )
            
            # Check for very long sentences
            long_sentences = sum(1 for wc in word_counts if wc > 40)
            if long_sentences > 0:
                score -= long_sentences * 5
                report.warnings.append(
                    f"{long_sentences} sentence(s) exceed 40 words"
                )
        
        # Word complexity (simple heuristic: long words ratio)
        words = full_text.split()
        if words:
            long_words = [w for w in words if len(w) > 12]
            long_word_ratio = len(long_words) / len(words)
            details["long_word_ratio"] = round(long_word_ratio, 3)
            
            if long_word_ratio > 0.15:
                score -= 10
                report.suggestions.append(
                    "Consider using simpler vocabulary where appropriate"
                )
        
        # Bullet point readability
        features = content.key_features.features
        long_features = [f for f in features if len(f.split()) > 10]
        if long_features:
            score -= len(long_features) * 3
            report.suggestions.append(
                "Keep key feature bullet points concise"
            )
        
        report.evaluation_details["readability"] = details
        return max(0, score)
    
    def _evaluate_fluency(
        self, 
        content: GeneratedContent,
        report: EvaluationReport,
    ) -> float:
        """
        Evaluate language fluency.
        
        Checks:
        - Basic grammar patterns
        - Language consistency
        - Natural phrasing
        """
        score = 100.0
        details = {}
        
        full_text = content.to_html()
        
        # Check for common issues
        issues_found = []
        
        # Repeated words (simple check)
        words = re.findall(r'\b\w+\b', full_text.lower())
        word_pairs = list(zip(words, words[1:]))
        repeated = [w for w, w2 in word_pairs if w == w2 and len(w) > 3]
        
        if repeated:
            score -= min(len(repeated) * 5, 20)
            details["repeated_words"] = repeated[:5]
            report.warnings.append(
                f"Found {len(repeated)} repeated consecutive words"
            )
        
        # Check for placeholder text
        placeholders = ["lorem", "ipsum", "[", "]", "TODO", "FIXME"]
        for placeholder in placeholders:
            if placeholder.lower() in full_text.lower():
                score -= 30
                report.add_critical_issue(f"Contains placeholder text: {placeholder}")
        
        # Check for mixed languages (basic check for common markers)
        language_markers = {
            Language.ENGLISH: [" the ", " and ", " for ", " with "],
            Language.PORTUGUESE: [" o ", " e ", " para ", " com "],
            Language.SPANISH: [" el ", " y ", " para ", " con "],
            Language.FRENCH: [" le ", " et ", " pour ", " avec "],
            Language.ITALIAN: [" il ", " e ", " per ", " con "],
        }
        
        expected_markers = language_markers.get(
            self.language, 
            language_markers[Language.ENGLISH]
        )
        
        other_languages = {
            lang: markers 
            for lang, markers in language_markers.items() 
            if lang != self.language
        }
        
        # Check if expected language markers are present
        expected_found = sum(
            1 for m in expected_markers if m in full_text.lower()
        )
        if expected_found < 2:
            score -= 15
            report.warnings.append(
                "Content may not be fully in the expected language"
            )
            details["language_marker_count"] = expected_found
        
        # Check for common grammar issues (language-specific)
        if self.language == Language.ENGLISH:
            # Double spaces
            if "  " in full_text:
                score -= 5
                report.suggestions.append("Remove double spaces")
            
            # Missing articles before nouns (simple heuristic)
            if re.search(r'\b(is|are|was|were)\s+[A-Z]', full_text):
                # Might indicate missing article, but too many false positives
                pass
        
        # Excessive punctuation
        excessive_punct = re.findall(r'[!?]{2,}', full_text)
        if excessive_punct:
            score -= len(excessive_punct) * 5
            report.suggestions.append("Avoid excessive punctuation marks")
        
        # All caps words (excluding HTML tags)
        text_only = re.sub(r'<[^>]+>', '', full_text)
        all_caps = re.findall(r'\b[A-Z]{4,}\b', text_only)
        if len(all_caps) > 2:
            score -= 10
            report.suggestions.append("Avoid excessive use of all-caps words")
        
        report.evaluation_details["fluency"] = details
        return max(0, score)
    
    def quick_validate(self, content: GeneratedContent) -> tuple[bool, list[str]]:
        """
        Perform quick validation without full evaluation.
        
        Returns:
            Tuple of (is_valid, list of critical issues)
        """
        issues = []
        
        # Check critical structure requirements
        if len(content.title.content) > 60:
            issues.append("Title exceeds 60 characters")
        
        if len(content.meta_description.content) > 155:
            issues.append("Meta description exceeds 155 characters")
        
        if len(content.description.content) < 400:
            issues.append("Description too short (min 400 characters)")
        
        if len(content.key_features.features) < 3:
            issues.append("Too few key features (min 3)")
        
        if not content.headline.content.strip():
            issues.append("Headline is empty")
        
        return (len(issues) == 0, issues)
    
    def compare(
        self, 
        content_a: GeneratedContent, 
        content_b: GeneratedContent,
    ) -> dict:
        """
        Compare two generated contents for the same property.
        
        Useful for A/B testing different tones or regenerations.
        
        Returns:
            Comparison dictionary with scores and winner
        """
        report_a = self.evaluate(content_a)
        report_b = self.evaluate(content_b)
        
        return {
            "content_a": {
                "overall_score": report_a.overall_score,
                "is_compliant": report_a.is_compliant,
                "language": report_a.language,
                "tone": report_a.tone,
            },
            "content_b": {
                "overall_score": report_b.overall_score,
                "is_compliant": report_b.is_compliant,
                "language": report_b.language,
                "tone": report_b.tone,
            },
            "winner": "a" if report_a.overall_score > report_b.overall_score else "b",
            "score_difference": abs(report_a.overall_score - report_b.overall_score),
        }

