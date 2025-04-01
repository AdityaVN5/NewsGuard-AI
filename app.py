%%writefile app.py
import os
import nltk
import html  # Standard HTML escaping
import requests
import time
import random
import gradio as gr
from minicheck.minicheck import MiniCheck
from fake_useragent import UserAgent
from bs4 import BeautifulSoup

# --- NLTK Download ---
try:
    nltk.data.find('tokenizers/punkt')
except nltk.downloader.DownloadError:
    print("Downloading NLTK 'punkt' tokenizer...")
    nltk.download('punkt')

# --- Configuration & Initialization ---
print("Testing html.escape directly after import:", html.escape("<b>Bold?</b>")) # Test escape

# Model Initialization
os.environ["CUDA_VISIBLE_DEVICES"] = os.environ.get("CUDA_VISIBLE_DEVICES", "0")
scorer = None
try:
    scorer = MiniCheck(model_name='flan-t5-large', cache_dir='./ckpts')
    print("MiniCheck model loaded successfully.")
except Exception as e:
    print(f"ERROR: Failed to initialize MiniCheck model: {e}")
    print("Fact-checking functionality will be disabled.")

# Web Scraping Config
SEARCH_URL = "https://duckduckgo.com/html/"
RATE_LIMIT = (7, 12)
RETRIES = 3
TIMEOUT = 15
PROXY_LIST = []

# User Agent Initialization
ua = None
try:
    ua = UserAgent()
    print("Fake UserAgent initialized.")
except Exception as e:
    print(f"Warning: Could not initialize fake_useragent. Using a default User-Agent. Error: {e}")
    class FallbackUserAgent:
        def random(self):
            return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    ua = FallbackUserAgent()

# --- Helper Functions ---

def get_random_proxy():
    return random.choice(PROXY_LIST) if PROXY_LIST else None

# --- Web Search Functions ---

def search_web(query):
    if not ua:
        print("ERROR: UserAgent not initialized. Cannot perform web search.")
        return None

    session = requests.Session()
    session.headers.update({
        'User-Agent': ua.random,
        'Referer': 'https://duckduckgo.com/',
        'Accept-Language': 'en-US,en;q=0.5'
    })
    params = {'q': query, 'kl': 'us-en'}

    for attempt in range(RETRIES):
        sleep_time = random.uniform(*RATE_LIMIT)
        print(f"Waiting for {sleep_time:.2f} seconds before attempt {attempt + 1}...")
        time.sleep(sleep_time)
        proxy = get_random_proxy()
        proxies = {'http': proxy, 'https': proxy} if proxy else None

        try:
            print(f"Attempt {attempt + 1}: Searching for '{query}'...")
            response = session.get(SEARCH_URL, params=params, proxies=proxies, timeout=TIMEOUT)
            response.raise_for_status()

            if "CAPTCHA" in response.text:
                print("CAPTCHA detected! Waiting longer...")
                time.sleep(random.uniform(60, 120))
                continue

            print(f"Attempt {attempt + 1} successful.")
            return response.text

        except requests.exceptions.Timeout:
            print(f"Attempt {attempt + 1} failed: Timeout after {TIMEOUT} seconds.")
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {e}")

    print(f"Failed to retrieve search results for '{query}' after {RETRIES} attempts.")
    return None

def parse_duckduckgo_results(html_content):
    if not html_content:
        return []
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        results = []
        # Updated selectors based on potential DDG HTML structures
        for res in soup.select('.result, .web-result, div.result'):
            title_tag = res.select_one('.result__title a, .result-title a, h2.result-title a')
            snippet_tag = res.select_one('.result__snippet, .result-snippet, div.result-snippet')
            link_tag = res.select_one('.result__url, .result-link, a.result-link') # Check link text source if needed

            title = title_tag.get_text(strip=True) if title_tag else 'N/A'
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else 'N/A'
            link = None

            # Prefer href from title tag, fall back to link tag's text or href
            if title_tag and title_tag.has_attr('href'):
                link = title_tag['href']
            elif link_tag and link_tag.has_attr('href'):
                link = link_tag['href']
            elif link_tag:
                link = link_tag.get_text(strip=True)


            # Basic filtering and cleaning
            if link and snippet != 'N/A' and not link.startswith('http://duckduckgo.com') and not link.startswith('/l/'):
                # TODO: Handle relative URLs if necessary (e.g., using urljoin)
                results.append({
                    'title': title,
                    'snippet': snippet,
                    'link': link.strip()
                })

        print(f"Parsed {len(results)} results.")
        return results
    except Exception as e:
        print(f"ERROR during HTML parsing: {e}")
        import traceback
        traceback.print_exc()
        return []


def search_trusted_sources(query):
    print(f"\n--- Searching web for claim: '{query}' ---")
    html_content = search_web(query)
    if not html_content:
        print("Failed to get HTML content from web search.")
        return []
    parsed = parse_duckduckgo_results(html_content)
    return parsed[:10] # Limit to top 10 results

# --- Credibility Assessment ---

def assess_credibility(claim, snippets):
    if not scorer:
        print("ERROR: MiniCheck model not loaded. Cannot assess credibility.")
        return {"status": "Error", "confidence": 0.0, "details": {"error_message": "Model not loaded", "all_probabilities": [], "predictions": []}}

    if not snippets:
        print("No snippets found to assess credibility.")
        return {"status": "Unverified", "confidence": 0.0, "details": {"all_probabilities": [], "predictions": []}}

    print(f"Assessing credibility for '{claim}' using {len(snippets)} snippets...")
    try:
        pred_labels, raw_probs, _, _ = scorer.score(docs=snippets, claims=[claim]*len(snippets), chunk_size=8)
        supported_probs = [p for label, p in zip(pred_labels, raw_probs) if label == 1]
        confidence = max(supported_probs) if supported_probs else 0.0

        if confidence >= 0.7:
            status = "Supported"
        elif any(label == 0 for label in pred_labels):
            status = "Contradicted"
        else:
            status = "Unverified"

        print(f"Assessment complete: Status='{status}', Confidence={confidence:.2f}")
        return {
            "status": status,
            "confidence": round(confidence, 2),
            "details": {
                "all_probabilities": [round(p, 2) for p in raw_probs],
                "predictions": pred_labels
            }
        }
    except Exception as e:
        print(f"ERROR during assess_credibility: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "Error", "confidence": 0.0, "details": {"error_message": str(e), "all_probabilities": [], "predictions": []}}

# --- Main Verification Workflow ---

def verify_news(text):
    if not text or not text.strip():
        print("Input text is empty.")
        return []

    claims = [claim.strip() for claim in text.split(';') if claim.strip()]
    if not claims:
        print("No valid claims found after splitting input.")
        return []

    print(f"\n=== Verifying {len(claims)} claim(s) ===")
    results = []

    for i, claim in enumerate(claims):
        print(f"\n[Claim {i+1}/{len(claims)}]")
        search_results = search_trusted_sources(claim)
        snippets = [res['snippet'] for res in search_results if res.get('snippet') and res.get('snippet') != 'N/A']

        if not snippets:
            print("No valid snippets obtained from search results.")
            assessment = {"status": "Unverified", "confidence": 0.0, "details": {"all_probabilities": [], "predictions": []}}
            # Add sources even if assessment failed, but mark probability as N/A
            final_sources = [{**source, 'probability': 'N/A'} for source in search_results]
        else:
            assessment = assess_credibility(claim, snippets)
            probabilities = assessment["details"]["all_probabilities"]
            # Match probabilities back to sources
            final_sources = []
            for idx, source in enumerate(search_results):
                source_data = source.copy()
                source_data["probability"] = probabilities[idx] if idx < len(probabilities) else 'N/A'
                final_sources.append(source_data)

        if assessment["status"] == "Contradicted":
            gr.Warning(f"🚨 Red Alert: The claim '{claim}' appears to be contradicted by available evidence.")

        results.append({
            "claim": claim,
            "status": assessment["status"],
            "confidence": assessment["confidence"],
            "sources": final_sources,
        })

    print("\n=== Verification Complete ===")
    return results

# --- Formatting for Gradio Output ---

def format_results(results):
    # Test html.escape within the function context too
    print("Testing html.escape inside format_results:", html.escape("<h1>Test</h1>"))

    if not results:
        # Return simple message if no results (e.g., empty input)
        return "<p style='color: gray; text-align: center; padding: 20px;'>Please enter a claim to analyze, or check logs for errors if input was provided.</p>"

    # Standardized CSS
    css = """
    <style>
        .header {text-align: center; padding: 20px; background: #f0f2f5; border-radius: 10px; margin-bottom: 20px; border: 1px solid #dee2e6;}
        .header h1 { margin: 0; color: #343a40; }
        .header p { margin: 5px 0 0; color: #6c757d; }
        .result-box {padding: 20px; margin: 20px 0; border-radius: 10px; background: white; box-shadow: 0 4px 8px rgba(0,0,0,0.05); border: 1px solid #e9ecef;}
        .supported {border-left: 5px solid #28a745;} /* Green */
        .contradicted {border-left: 5px solid #dc3545;} /* Red */
        .unverified {border-left: 5px solid #ffc107;} /* Yellow */
        .error {border-left: 5px solid #6c757d;} /* Gray */
        .result-box h3 { margin-top: 0; color: #495057; font-size: 1.2em; margin-bottom: 10px;}
        .verdict-section { margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid #f1f3f5;}
        .verdict-section strong { font-size: 1.1em; }
        .status-text-supported { color: #28a745; font-weight: bold; }
        .status-text-contradicted { color: #dc3545; font-weight: bold; }
        .status-text-unverified { color: #ffc107; font-weight: bold; }
        .status-text-error { color: #6c757d; font-weight: bold; }
        .confidence-bar {height: 10px; background: #e9ecef; border-radius: 5px; margin: 8px 0; overflow: hidden;}
        .confidence-fill-supported {height: 100%; border-radius: 5px; background: #28a745;}
        .confidence-fill-contradicted {height: 100%; border-radius: 5px; background: #dc3545;}
        .confidence-fill-unverified {height: 100%; border-radius: 5px; background: #ffc107;}
        .confidence-fill-error {height: 100%; border-radius: 5px; background: #6c757d;}
        .sources-header { margin-top: 15px; margin-bottom: 10px; color: #495057; font-weight: bold; font-size: 1.1em; border-top: 1px solid #f1f3f5; padding-top: 15px;}
        .source-card {padding: 15px; margin-bottom: 10px; background: #f8f9fa; border-radius: 8px; border: 1px solid #e9ecef;}
        .source-card p { margin: 5px 0; font-size: 0.95em; line-height: 1.4;}
        .source-card strong { color: #343a40; }
        .source-footer { margin-top: 10px; display: flex; justify-content: space-between; align-items: center; font-size: 0.9em;}
        .source-link { color: #007bff; text-decoration: none; font-weight: 500;}
        .source-link:hover { text-decoration: underline; }
        .source-prob { color: #6c757d; background-color: #e9ecef; padding: 2px 6px; border-radius: 4px; font-size: 0.85em;}
    </style>
    """

    html_output = css
    for result in results:
        try:
            # Use html.escape for dynamic content
            claim_html = html.escape(result.get('claim', 'N/A'))
            status = result.get('status', 'Error').lower()
            confidence = result.get('confidence', 0.0)
            confidence_percent = confidence * 100
            status_display = html.escape(result.get('status', 'Error')) # Escape status text

            status_text_class = f"status-text-{status}"
            confidence_fill_class = f"confidence-fill-{status}"

            html_output += f"""
            <div class="result-box {status}">
                <h3>Claim: {claim_html}</h3>
                <div class="verdict-section">
                    <strong>Verdict:</strong> <span class="{status_text_class}">{status_display}</span>
                    <div class="confidence-bar">
                        <div class="{confidence_fill_class}" style="width: {confidence_percent:.0f}%"></div>
                    </div>
                    <span>Confidence Score: {confidence:.2f}</span>
                </div>
                <div class="sources-header">Supporting Evidence / Sources:</div>
            """

            sources = result.get("sources", [])
            if not sources:
                html_output += "<p style='color: gray; font-style: italic;'>No specific sources were found or analyzed for this claim.</p>"
            else:
                for source in sources:
                    title_html = html.escape(source.get('title', 'No Title Provided'))
                    snippet_html = html.escape(source.get('snippet', 'No Snippet Available'))
                    link_url = source.get('link', '#')
                    # Escape the URL for use in the href attribute
                    link_href_html = html.escape(link_url)

                    prob = source.get('probability', 'N/A')
                    prob_display = f"{prob:.2f}" if isinstance(prob, (float, int)) else html.escape(str(prob))

                    html_output += f"""
                    <div class="source-card">
                        <p><strong>{title_html}</strong></p>
                        <p>{snippet_html}</p>
                        <div class="source-footer">
                            <a href="{link_href_html}" target="_blank" class="source-link" rel="noopener noreferrer">
                                🔗 Visit Source
                            </a>
                            <span class="source-prob">AI Score: {prob_display}</span>
                        </div>
                    </div>
                    """
            html_output += "</div>" # Close result-box

        except Exception as e_fmt:
            print(f"ERROR during formatting result for claim '{result.get('claim', 'UNKNOWN')}': {e_fmt}")
            # Add a fallback message in the HTML output for this specific result
            html_output += f"<div class='result-box error'><p>Error formatting result for claim: {html.escape(result.get('claim', 'UNKNOWN'))}. Please check logs.</p></div>"


    return html_output


# --- Gradio Interface Definition ---

with gr.Blocks(theme=gr.themes.Soft(primary_hue=gr.themes.colors.blue, secondary_hue=gr.themes.colors.sky), title="NewsGuard AI") as demo:
    gr.Markdown("""
    <div class="header">
        <h1>🛡️ NewsGuard AI</h1>
        <p>Enter news claims (separated by semicolons ';') to analyze their credibility using AI and web search.</p>
    </div>
    """)

    with gr.Row():
        with gr.Column(scale=2):
            input_box = gr.Textbox(
                label="Enter News Claim(s)",
                placeholder="Example: The Eiffel Tower is in Berlin; Water boils at 100°C at sea level.",
                lines=6,
                elem_id="input-box"
            )
            gr.Examples(
                examples=[
                    ["COVID-19 vaccines contain microchips; The Great Wall of China is visible from the Moon"],
                    ["Drinking lemon water cures cancer; Climate change is primarily caused by human activity"],
                    ["The Earth is flat"],
                    ["The 2024 Olympics were held in Paris"],
                    ["Large Language Models can replace all human jobs next year"]
                ],
                inputs=input_box,
                label="Example Claims (click to use)"
            )
            submit_btn = gr.Button("🔍 Analyze Credibility", variant="primary")

        with gr.Column(scale=3):
            output_panel = gr.HTML(label="Analysis Results", elem_id="results-panel")

    # Define click action chain
    submit_btn.click(
        fn=verify_news,
        inputs=input_box,
        outputs=output_panel, # Temporarily output raw results here
        api_name="verify"
    ).then(
        fn=format_results,     # Format the raw results from the previous step
        inputs=output_panel,   # Input is the output of verify_news
        outputs=output_panel   # Output the formatted HTML back to the same panel
    )

# --- Main Execution ---

if __name__ == "__main__":
    print("Starting Gradio App Server...")
    # share=True creates a public link. Set to False for local-only access.
    # server_name="0.0.0.0" allows access from other devices on the same network.
    demo.launch(share=True)
    print("Gradio App Server Stopped.")