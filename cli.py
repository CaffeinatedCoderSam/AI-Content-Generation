"""Command-line interface for the real estate content generator."""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

from .models.property import PropertyInput, Language, Tone, ListingType
from .models.content import GeneratedContent
from .generators.openai_generator import OpenAIContentGenerator, MockContentGenerator
from .evaluation.quality import ContentEvaluator
from .config import get_config


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="AI-powered real estate content generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate from JSON file
  python -m src.cli --input property.json --output content.html

  # Generate with specific language and tone
  python -m src.cli --input property.json --language pt --tone luxury

  # Use mock generator for testing (no API calls)
  python -m src.cli --input property.json --mock

  # Evaluate existing content
  python -m src.cli --input property.json --content content.html --evaluate
        """,
    )
    
    # Input/output
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input JSON file with property data",
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file path (default: stdout)",
    )
    
    # Generation options
    parser.add_argument(
        "--language", "-l",
        choices=["en", "pt", "es", "fr", "it"],
        help="Output language (overrides JSON input)",
    )
    parser.add_argument(
        "--tone", "-t",
        choices=["formal", "friendly", "luxury", "investor"],
        help="Content tone (overrides JSON input)",
    )
    
    # Model options
    parser.add_argument(
        "--model", "-m",
        default="gpt-4o",
        help="OpenAI model to use (default: gpt-4o)",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Generation temperature (default: 0.7)",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock generator (no API calls)",
    )
    
    # Evaluation
    parser.add_argument(
        "--evaluate", "-e",
        action="store_true",
        help="Evaluate generated content and show report",
    )
    parser.add_argument(
        "--content", "-c",
        help="Existing content file to evaluate (requires --evaluate)",
    )
    
    # Output format
    parser.add_argument(
        "--format", "-f",
        choices=["html", "json", "both"],
        default="html",
        help="Output format (default: html)",
    )
    
    # Verbosity
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress non-essential output",
    )
    
    return parser.parse_args()


def load_property_input(
    file_path: str,
    language_override: Optional[str] = None,
    tone_override: Optional[str] = None,
) -> PropertyInput:
    """Load and validate property input from JSON file."""
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Apply overrides
    if language_override:
        data["language"] = language_override
    if tone_override:
        data["tone"] = tone_override
    
    return PropertyInput(**data)


def output_content(
    content: GeneratedContent,
    output_path: Optional[str],
    output_format: str,
) -> None:
    """Output generated content to file or stdout."""
    if output_format == "html":
        output_text = content.to_html()
    elif output_format == "json":
        output_text = json.dumps(content.to_dict(), indent=2, ensure_ascii=False)
    else:  # both
        output_text = f"=== HTML Output ===\n{content.to_html()}\n\n"
        output_text += f"=== JSON Output ===\n{json.dumps(content.to_dict(), indent=2, ensure_ascii=False)}"
    
    if output_path:
        path = Path(output_path)
        path.write_text(output_text, encoding="utf-8")
        print(f"Content written to: {output_path}", file=sys.stderr)
    else:
        print(output_text)


def print_evaluation_report(report, verbose: bool = False) -> None:
    """Print evaluation report to stderr."""
    print("\n" + "=" * 50, file=sys.stderr)
    print("CONTENT EVALUATION REPORT", file=sys.stderr)
    print("=" * 50, file=sys.stderr)
    
    print(f"\nOverall Score: {report.overall_score:.1f}/100", file=sys.stderr)
    print(f"Compliant: {'✓ Yes' if report.is_compliant else '✗ No'}", file=sys.stderr)
    
    print("\nComponent Scores:", file=sys.stderr)
    print(f"  • Structure:   {report.structure_score:.1f}/100", file=sys.stderr)
    print(f"  • SEO:         {report.seo_score:.1f}/100", file=sys.stderr)
    print(f"  • Readability: {report.readability_score:.1f}/100", file=sys.stderr)
    print(f"  • Fluency:     {report.fluency_score:.1f}/100", file=sys.stderr)
    
    if report.critical_issues:
        print("\n❌ Critical Issues:", file=sys.stderr)
        for issue in report.critical_issues:
            print(f"  • {issue}", file=sys.stderr)
    
    if report.warnings:
        print("\n⚠️  Warnings:", file=sys.stderr)
        for warning in report.warnings:
            print(f"  • {warning}", file=sys.stderr)
    
    if report.suggestions and verbose:
        print("\n💡 Suggestions:", file=sys.stderr)
        for suggestion in report.suggestions:
            print(f"  • {suggestion}", file=sys.stderr)
    
    if verbose and report.seo_analysis:
        print("\nSEO Details:", file=sys.stderr)
        print(f"  Keywords found: {', '.join(report.seo_analysis.keywords_found)}", file=sys.stderr)
        if report.seo_analysis.keywords_missing:
            print(f"  Keywords missing: {', '.join(report.seo_analysis.keywords_missing)}", file=sys.stderr)
        print(f"  Keyword density: {report.seo_analysis.keyword_density:.2f}%", file=sys.stderr)
    
    print("\n" + "=" * 50, file=sys.stderr)


async def main_async(args: argparse.Namespace) -> int:
    """Async main function."""
    try:
        # Load property data
        if not args.quiet:
            print(f"Loading property data from: {args.input}", file=sys.stderr)
        
        property_data = load_property_input(
            args.input,
            language_override=args.language,
            tone_override=args.tone,
        )
        
        if args.verbose:
            print(f"Property: {property_data.title}", file=sys.stderr)
            print(f"Location: {property_data.location.city}", file=sys.stderr)
            print(f"Language: {property_data.language.value}", file=sys.stderr)
            print(f"Tone: {property_data.tone.value}", file=sys.stderr)
        
        # Create generator
        if args.mock:
            if not args.quiet:
                print("Using mock generator (no API calls)", file=sys.stderr)
            generator = MockContentGenerator()
        else:
            config = get_config()
            if not config.openai.api_key:
                print("Error: OPENAI_API_KEY environment variable not set", file=sys.stderr)
                return 1
            generator = OpenAIContentGenerator(
                api_key=config.openai.api_key,
                model=args.model,
                temperature=args.temperature,
            )
            
            # Show cost estimate
            if not args.quiet:
                cost = generator.estimate_cost(property_data)
                print(f"Estimated cost: ${cost:.4f}", file=sys.stderr)
        
        # Generate content
        if not args.quiet:
            print("Generating content...", file=sys.stderr)
        
        content = await generator.generate(property_data)
        
        if not args.quiet:
            print("Content generated successfully!", file=sys.stderr)
        
        # Evaluate if requested
        if args.evaluate:
            evaluator = ContentEvaluator(property_data)
            report = evaluator.evaluate(content)
            print_evaluation_report(report, verbose=args.verbose)
        
        # Output content
        output_content(content, args.output, args.format)
        
        return 0
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in input file: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def main() -> int:
    """Main entry point."""
    args = parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    sys.exit(main())

