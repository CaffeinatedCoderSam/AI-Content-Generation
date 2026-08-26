"""Streamlit interactive UI for the real estate content generator."""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Optional

# Add project root to path for Streamlit compatibility
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st

from src.models.property import PropertyInput, Language, Tone, ListingType, Location, Features
from src.generators.openai_generator import OpenAIContentGenerator, MockContentGenerator
from src.evaluation.quality import ContentEvaluator


# ============================================================================
# Constants
# ============================================================================

LANGUAGE_OPTIONS = {
    "en": {"name": "English", "flag": "🇬🇧"},
    "pt": {"name": "Portuguese", "flag": "🇵🇹"},
    "es": {"name": "Spanish", "flag": "🇪🇸"},
    "fr": {"name": "French", "flag": "🇫🇷"},
    "it": {"name": "Italian", "flag": "🇮🇹"},
}


# ============================================================================
# Page Configuration
# ============================================================================

st.set_page_config(
    page_title="Real Estate Content Generator",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
    }
    .score-card {
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .score-good { background-color: #d4edda; }
    .score-warning { background-color: #fff3cd; }
    .score-bad { background-color: #f8d7da; }
    .html-preview {
        background-color: #1e1e1e;
        color: #d4d4d4;
        padding: 20px;
        border-radius: 8px;
        font-family: 'Consolas', monospace;
        white-space: pre-wrap;
        overflow-x: auto;
    }
    code {
        color: #569cd6;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# Session State Initialization
# ============================================================================

def init_session_state():
    """Initialize session state variables."""
    if "generated_contents" not in st.session_state:
        st.session_state.generated_contents = {}  # Dict of lang -> content
    if "evaluation_reports" not in st.session_state:
        st.session_state.evaluation_reports = {}  # Dict of lang -> report
    if "property_data" not in st.session_state:
        st.session_state.property_data = None
    if "selected_languages" not in st.session_state:
        st.session_state.selected_languages = ["en"]


# ============================================================================
# Helper Functions
# ============================================================================

def run_async(coro):
    """Run async function in sync context."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def get_score_color(score: float) -> str:
    """Get color class based on score."""
    if score >= 80:
        return "score-good"
    elif score >= 60:
        return "score-warning"
    return "score-bad"


def render_score_card(label: str, score: float):
    """Render a score card with color coding."""
    color_class = get_score_color(score)
    emoji = "✅" if score >= 80 else "⚠️" if score >= 60 else "❌"
    st.markdown(f"""
    <div class="score-card {color_class}">
        <h3>{emoji} {label}</h3>
        <h2>{score:.1f}/100</h2>
    </div>
    """, unsafe_allow_html=True)


def generate_multilingual_html(contents: dict) -> str:
    """
    Generate HTML with language switcher.
    
    Args:
        contents: Dict of language code -> GeneratedContent
        
    Returns:
        Complete HTML string with language switcher
    """
    if not contents:
        return ""
    
    # Get list of available languages
    available_langs = list(contents.keys())
    default_lang = available_langs[0]
    
    # Build language switcher buttons
    lang_buttons = []
    for lang_code in available_langs:
        lang_info = LANGUAGE_OPTIONS.get(lang_code, {"name": lang_code, "flag": "🌐"})
        lang_buttons.append(
            f'<button class="lang-btn" data-lang="{lang_code}" onclick="switchLanguage(\'{lang_code}\')">'
            f'{lang_info["flag"]} {lang_info["name"]}</button>'
        )
    
    lang_switcher_html = " ".join(lang_buttons)
    
    # Build content sections for each language
    content_sections = []
    for lang_code, content in contents.items():
        display = "block" if lang_code == default_lang else "none"
        
        section_html = f'''
<div class="lang-content" data-lang="{lang_code}" style="display: {display};">
{content.title.to_html()}

{content.meta_description.to_html()}

{content.headline.to_html()}

{content.description.to_html()}

{content.key_features.to_html()}

{content.neighborhood.to_html()}

{content.call_to_action.to_html()}
</div>'''
        content_sections.append(section_html)
    
    all_content = "\n".join(content_sections)
    
    # Complete HTML with styles and JavaScript
    html = f'''<!DOCTYPE html>
<html lang="{default_lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {{
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }}
        .language-switcher {{
            position: fixed;
            top: 20px;
            right: 20px;
            display: flex;
            gap: 8px;
            background: white;
            padding: 10px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            z-index: 1000;
        }}
        .lang-btn {{
            padding: 8px 16px;
            border: 1px solid #ddd;
            background: white;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s;
        }}
        .lang-btn:hover {{
            background: #f5f5f5;
        }}
        .lang-btn.active {{
            background: #2563eb;
            color: white;
            border-color: #2563eb;
        }}
        h1 {{
            color: #1a1a1a;
            font-size: 2rem;
            margin-top: 60px;
        }}
        section {{
            margin: 24px 0;
        }}
        section p {{
            color: #555;
        }}
        ul {{
            padding-left: 20px;
        }}
        li {{
            margin: 8px 0;
        }}
        .call-to-action {{
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            font-weight: 500;
            margin-top: 30px;
        }}
        @media (max-width: 768px) {{
            .language-switcher {{
                position: static;
                margin-bottom: 20px;
                justify-content: center;
            }}
            h1 {{
                margin-top: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="language-switcher">
        {lang_switcher_html}
    </div>
    
    {all_content}
    
    <script>
        function switchLanguage(lang) {{
            // Hide all content sections
            document.querySelectorAll('.lang-content').forEach(el => {{
                el.style.display = 'none';
            }});
            
            // Show selected language content
            document.querySelector('.lang-content[data-lang="' + lang + '"]').style.display = 'block';
            
            // Update button states
            document.querySelectorAll('.lang-btn').forEach(btn => {{
                btn.classList.remove('active');
            }});
            document.querySelector('.lang-btn[data-lang="' + lang + '"]').classList.add('active');
            
            // Update html lang attribute
            document.documentElement.lang = lang;
        }}
        
        // Set initial active state
        document.querySelector('.lang-btn[data-lang="{default_lang}"]').classList.add('active');
    </script>
</body>
</html>'''
    
    return html


# ============================================================================
# Main UI
# ============================================================================

def main():
    """Main Streamlit application."""
    init_session_state()
    
    # Header
    st.title("🏠 Real Estate Content Generator")
    st.markdown("""
    Generate SEO-optimized, multilingual content for property listings using AI.
    """)
    
    # Sidebar - Configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            value=os.getenv("OPENAI_API_KEY", ""),
            help="Enter your OpenAI API key or set OPENAI_API_KEY environment variable",
        )
        
        use_mock = st.checkbox(
            "Use Mock Generator (No API calls)",
            value=not bool(api_key),
            help="Use mock generator for testing without API calls",
        )
        
        st.divider()
        
        # Model settings
        st.subheader("Model Settings")
        model = st.selectbox(
            "Model",
            ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
            help="Select OpenAI model to use",
        )
        
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=0.7,
            step=0.1,
            help="Higher values = more creative, lower = more focused",
        )
        
        st.divider()
        
        # Language MULTI-SELECT
        st.subheader("Output Settings")
        
        language_options = [
            f"{info['flag']} {info['name']} ({code})" 
            for code, info in LANGUAGE_OPTIONS.items()
        ]
        
        selected_languages = st.multiselect(
            "Languages",
            options=language_options,
            default=["🇬🇧 English (en)"],
            help="Select one or more languages to generate content in",
        )
        
        # Extract language codes from selection
        selected_lang_codes = []
        for sel in selected_languages:
            for code in LANGUAGE_OPTIONS.keys():
                if f"({code})" in sel:
                    selected_lang_codes.append(code)
                    break
        
        if not selected_lang_codes:
            selected_lang_codes = ["en"]
        
        st.session_state.selected_languages = selected_lang_codes
        
        # Show selected count
        st.caption(f"📝 Will generate in {len(selected_lang_codes)} language(s)")
        
        tone = st.selectbox(
            "Tone",
            [
                ("Friendly", "friendly"),
                ("Formal", "formal"),
                ("Luxury", "luxury"),
                ("Investor-focused", "investor"),
            ],
            format_func=lambda x: x[0],
        )
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["📝 Input", "📄 Output", "📊 Evaluation"])
    
    # ========== TAB 1: Input ==========
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Property Details")
            
            title = st.text_input(
                "Property Title",
                value="T3 apartment in Lisbon",
                help="e.g., 'Modern T3 apartment in central location'",
            )
            
            listing_type = st.radio(
                "Listing Type",
                ["sale", "rent"],
                horizontal=True,
            )
            
            price = st.number_input(
                "Price (€)",
                min_value=1000,
                max_value=100000000,
                value=650000,
                step=5000,
            )
            
            st.subheader("Location")
            city = st.text_input("City", value="Lisbon")
            neighborhood = st.text_input("Neighborhood", value="Campo de Ourique")
        
        with col2:
            st.subheader("Features")
            
            col_a, col_b = st.columns(2)
            with col_a:
                bedrooms = st.number_input("Bedrooms", min_value=0, max_value=20, value=3)
                bathrooms = st.number_input("Bathrooms", min_value=0, max_value=10, value=2)
                area_sqm = st.number_input("Area (sqm)", min_value=10, max_value=10000, value=120)
                floor = st.number_input("Floor", min_value=0, max_value=100, value=2)
            
            with col_b:
                year_built = st.number_input(
                    "Year Built",
                    min_value=1800,
                    max_value=2025,
                    value=2005,
                )
                
                balcony = st.checkbox("Balcony", value=True)
                parking = st.checkbox("Parking", value=False)
                elevator = st.checkbox("Elevator", value=True)
        
        # Additional features
        with st.expander("Additional Features"):
            col_c, col_d = st.columns(2)
            with col_c:
                garden = st.checkbox("Garden")
                pool = st.checkbox("Swimming Pool")
                terrace = st.checkbox("Terrace")
                storage = st.checkbox("Storage Room")
            with col_d:
                air_conditioning = st.checkbox("Air Conditioning")
                heating = st.checkbox("Central Heating")
                furnished = st.checkbox("Furnished")
                renovated = st.checkbox("Recently Renovated")
        
        # Extra description
        description_extra = st.text_area(
            "Additional Details (optional)",
            placeholder="Add any extra details to include in the description...",
            height=100,
        )
        
        # JSON Input option
        with st.expander("📋 JSON Input (Advanced)"):
            st.markdown("Paste property JSON directly:")
            json_input = st.text_area(
                "JSON Input",
                height=200,
                placeholder='{"title": "...", "location": {...}, "features": {...}}',
            )
            
            if st.button("Load from JSON"):
                try:
                    data = json.loads(json_input)
                    st.success("JSON loaded successfully!")
                    st.json(data)
                except json.JSONDecodeError as e:
                    st.error(f"Invalid JSON: {e}")
        
        st.divider()
        
        # Generate button
        if st.button("🚀 Generate Content", type="primary", use_container_width=True):
            if not selected_lang_codes:
                st.error("Please select at least one language")
            else:
                try:
                    # Create generator
                    if use_mock or not api_key:
                        generator = MockContentGenerator()
                        st.info("Using mock generator (no API calls)")
                    else:
                        generator = OpenAIContentGenerator(
                            api_key=api_key,
                            model=model,
                            temperature=temperature,
                        )
                    
                    # Clear previous results
                    st.session_state.generated_contents = {}
                    st.session_state.evaluation_reports = {}
                    
                    # Generate for each language
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for i, lang_code in enumerate(selected_lang_codes):
                        lang_info = LANGUAGE_OPTIONS[lang_code]
                        status_text.text(f"Generating {lang_info['flag']} {lang_info['name']}...")
                        
                        # Build property input for this language
                        property_data = PropertyInput(
                            title=title,
                            location=Location(
                                city=city,
                                neighborhood=neighborhood if neighborhood else None,
                            ),
                            features=Features(
                                bedrooms=bedrooms,
                                bathrooms=bathrooms,
                                area_sqm=area_sqm,
                                balcony=balcony,
                                parking=parking,
                                elevator=elevator,
                                floor=floor,
                                year_built=year_built,
                                garden=garden,
                                pool=pool,
                                terrace=terrace,
                                storage=storage,
                                air_conditioning=air_conditioning,
                                heating=heating,
                                furnished=furnished,
                                renovated=renovated,
                            ),
                            price=price,
                            listing_type=ListingType(listing_type),
                            language=Language(lang_code),
                            tone=Tone(tone[1]),
                            description_extra=description_extra if description_extra else None,
                        )
                        
                        # Generate content
                        content = run_async(generator.generate(property_data))
                        st.session_state.generated_contents[lang_code] = content
                        
                        # Evaluate
                        evaluator = ContentEvaluator(property_data)
                        report = evaluator.evaluate(content)
                        st.session_state.evaluation_reports[lang_code] = report
                        
                        progress_bar.progress((i + 1) / len(selected_lang_codes))
                    
                    status_text.empty()
                    progress_bar.empty()
                    
                    st.success(f"✅ Content generated in {len(selected_lang_codes)} language(s)!")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"Error: {e}")
    
    # ========== TAB 2: Output ==========
    with tab2:
        if st.session_state.generated_contents:
            st.subheader("Generated Content")
            
            # Language tabs for output
            lang_tabs = []
            for lang_code in st.session_state.generated_contents.keys():
                lang_info = LANGUAGE_OPTIONS.get(lang_code, {"name": lang_code, "flag": "🌐"})
                lang_tabs.append(f"{lang_info['flag']} {lang_info['name']}")
            
            if len(lang_tabs) > 1:
                output_lang_tabs = st.tabs(lang_tabs)
                
                for idx, (lang_code, content) in enumerate(st.session_state.generated_contents.items()):
                    with output_lang_tabs[idx]:
                        render_content_output(content, lang_code)
            else:
                # Single language - no tabs needed
                lang_code = list(st.session_state.generated_contents.keys())[0]
                content = st.session_state.generated_contents[lang_code]
                render_content_output(content, lang_code)
            
            # Download combined HTML with language switcher
            st.divider()
            st.subheader("📥 Download Options")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Combined HTML with language switcher
                combined_html = generate_multilingual_html(st.session_state.generated_contents)
                st.download_button(
                    "📥 Download HTML (with Language Switcher)",
                    combined_html,
                    file_name="listing_multilingual.html",
                    mime="text/html",
                    help="Download a single HTML file with all languages and a switcher",
                )
            
            with col2:
                # Download all as JSON
                all_content_json = {
                    lang: content.to_dict() 
                    for lang, content in st.session_state.generated_contents.items()
                }
                st.download_button(
                    "📥 Download All (JSON)",
                    json.dumps(all_content_json, indent=2, ensure_ascii=False),
                    file_name="listing_all_languages.json",
                    mime="application/json",
                )
            
            with col3:
                if st.button("🔄 Regenerate All"):
                    st.rerun()
        
        else:
            st.info("👈 Fill in property details and click 'Generate Content' to see output.")
    
    # ========== TAB 3: Evaluation ==========
    with tab3:
        if st.session_state.evaluation_reports:
            st.subheader("Content Quality Reports")
            
            # Language tabs for evaluation
            if len(st.session_state.evaluation_reports) > 1:
                eval_lang_tabs = []
                for lang_code in st.session_state.evaluation_reports.keys():
                    lang_info = LANGUAGE_OPTIONS.get(lang_code, {"name": lang_code, "flag": "🌐"})
                    eval_lang_tabs.append(f"{lang_info['flag']} {lang_info['name']}")
                
                eval_tabs = st.tabs(eval_lang_tabs)
                
                for idx, (lang_code, report) in enumerate(st.session_state.evaluation_reports.items()):
                    with eval_tabs[idx]:
                        render_evaluation_report(report, lang_code)
            else:
                # Single language
                lang_code = list(st.session_state.evaluation_reports.keys())[0]
                report = st.session_state.evaluation_reports[lang_code]
                render_evaluation_report(report, lang_code)
        
        else:
            st.info("👈 Generate content to see evaluation report.")


def render_content_output(content, lang_code: str):
    """Render content output for a single language."""
    # Output format selector
    output_format = st.radio(
        "View Format",
        ["HTML Preview", "Raw HTML", "JSON", "Sections"],
        horizontal=True,
        key=f"format_{lang_code}",
    )
    
    if output_format == "HTML Preview":
        st.markdown("### Preview")
        st.markdown(f"**Title:** {content.title.content}")
        st.markdown(f"**Meta Description:** {content.meta_description.content}")
        st.markdown(f"## {content.headline.content}")
        st.markdown(content.description.content)
        st.markdown("### Key Features")
        for feature in content.key_features.features:
            st.markdown(f"- {feature}")
        st.markdown("### Neighborhood")
        st.markdown(content.neighborhood.content)
        st.markdown(f"*{content.call_to_action.content}*")
    
    elif output_format == "Raw HTML":
        st.code(content.to_html(), language="html")
    
    elif output_format == "JSON":
        st.json(content.to_dict())
    
    else:  # Sections
        with st.expander("Title", expanded=True):
            st.code(content.title.to_html(), language="html")
            st.caption(f"Length: {len(content.title.content)}/60 characters")
        
        with st.expander("Meta Description", expanded=True):
            st.code(content.meta_description.to_html(), language="html")
            st.caption(f"Length: {len(content.meta_description.content)}/155 characters")
        
        with st.expander("Headline", expanded=True):
            st.code(content.headline.to_html(), language="html")
        
        with st.expander("Description", expanded=True):
            st.code(content.description.to_html(), language="html")
            st.caption(f"Length: {len(content.description.content)} characters (target: 500-700)")
        
        with st.expander("Key Features", expanded=True):
            st.code(content.key_features.to_html(), language="html")
            st.caption(f"Count: {len(content.key_features.features)} features")
        
        with st.expander("Neighborhood", expanded=True):
            st.code(content.neighborhood.to_html(), language="html")
        
        with st.expander("Call to Action", expanded=True):
            st.code(content.call_to_action.to_html(), language="html")


def render_evaluation_report(report, lang_code: str):
    """Render evaluation report for a single language."""
    # Overall score
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        render_score_card("Overall", report.overall_score)
    with col2:
        render_score_card("Structure", report.structure_score)
    with col3:
        render_score_card("SEO", report.seo_score)
    with col4:
        render_score_card("Readability", report.readability_score)
    with col5:
        render_score_card("Fluency", report.fluency_score)
    
    st.divider()
    
    # Compliance status
    if report.is_compliant:
        st.success("✅ Content is compliant with all requirements")
    else:
        st.error("❌ Content has compliance issues")
    
    # Issues and recommendations
    col1, col2 = st.columns(2)
    
    with col1:
        if report.critical_issues:
            st.markdown("### ❌ Critical Issues")
            for issue in report.critical_issues:
                st.error(issue)
        
        if report.warnings:
            st.markdown("### ⚠️ Warnings")
            for warning in report.warnings:
                st.warning(warning)
    
    with col2:
        if report.suggestions:
            st.markdown("### 💡 Suggestions")
            for suggestion in report.suggestions:
                st.info(suggestion)
    
    # SEO Details
    if report.seo_analysis:
        with st.expander("🔍 SEO Analysis Details"):
            seo = report.seo_analysis
            
            st.markdown("**Keywords Found:**")
            if seo.keywords_found:
                st.write(", ".join(seo.keywords_found))
            else:
                st.write("None")
            
            st.markdown("**Keywords Missing:**")
            if seo.keywords_missing:
                st.write(", ".join(seo.keywords_missing))
            else:
                st.write("None")
            
            st.markdown(f"**Keyword Density:** {seo.keyword_density:.2f}%")
    
    # Detailed report
    with st.expander("📋 Full Report (JSON)"):
        st.json(report.to_dict())


if __name__ == "__main__":
    main()
