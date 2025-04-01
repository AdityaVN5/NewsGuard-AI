# 🛡️NewsGuard AI

## Overview

NewsGuard AI is a tool designed to assess the credibility of news claims using a combination of web search and AI-powered analysis. It leverages web scraping techniques to gather information from trusted sources and the MiniCheck library to evaluate the veracity of claims. This project aims to help users quickly identify potentially unreliable information and make better-informed decisions about the news they consume.

## Features

* **Claim Verification:** Analyzes user-provided news claims to determine their credibility.
* **Web Search Integration:** Scrapes search results from DuckDuckGo to gather supporting evidence for claims.
* **AI-Powered Assessment:** Utilizes the MiniCheck library, a fact-checking model, to assess the credibility of claims based on retrieved information.
* **Confidence Scoring:** Provides a confidence score indicating the reliability of the assessment.
* **User-Friendly Interface:** A Gradio interface allows users to easily input claims and view analysis results.
* **Clear Output Formatting:** Presents credibility assessments with supporting evidence and source information in an organized and easy-to-understand format.
* **Red Alert for Contradicted Claims:** Alerts the user with a warning message when a claim is contradicted by the analysis.

## Technologies Used

* Python 3.x
* Gradio
* MiniCheck
* Requests
* Fake-useragent
* Beautiful Soup 4
* NLTK
* HTML

### Setup and Installation

This project uses a Google Colaboratory notebook for the main news credibility analysis and a separate Python file (`app.py`) to run the Gradio user interface. Here's how to set it up:

1.  **Open the Colab Notebook:**

    * Open the `NewsGuard AI.ipynb` notebook in Google Colaboratory.
    * This notebook contains the core logic for web scraping, data processing, and credibility assessment.

2.  **Set up the Colab Environment:**

    * **Install Dependencies:** Run the cells in the Colab notebook to install the necessary Python packages. These typically include:

        ```bash
        !pip install requests fake-useragent beautifulsoup4 "minicheck @ git+[https://github.com/Liyan06/MiniCheck.git@main](https://github.com/Liyan06/MiniCheck.git@main)" gradio
        !pip install nltk
        ```

    * **Download NLTK Data:** You might need to download the NLTK 'punkt' tokenizer. Add these lines in your Colab notebook and run it.

        ```python
        import nltk
        try:
            nltk.data.find('tokenizers/punkt')
        except nltk.downloader.DownloadError:
            nltk.download('punkt')
        ```

    * **Run the Analysis:** Execute the cells in the Colab notebook to perform the news credibility analysis. You can modify the notebook to analyze different news claims.

3.  **Set up the Gradio Interface (Optional):**

    * If you want to use the Gradio interface, you'll need to run the `app.py` file. This file provides a user-friendly web interface to interact with the news verification functions.
    * **Install Dependencies (if running `app.py` locally):** If you plan to run `app.py` locally, ensure you have Python 3.x installed and install the required packages:

        ```bash
        pip install -r requirements.txt
        ```

        * Alternatively, you can install the dependencies directly:

            ```bash
            pip install gradio requests fake-useragent beautifulsoup4 minicheck nltk
            ```

    * **Run the Gradio App:** To launch the Gradio interface, execute the following command in your terminal:

        ```bash
        python app.py
        ```

        * This will start a local server, and you can access the interface via the displayed URL.
        
        
## Working Screenshots
![Screenshots/Screenshot 2025-04-01 212157.png](https://github.com/AdityaVN5/NewsGuard-AI/blob/main/Screenshots/Screenshot%202025-04-01%20212157.png)
![](https://github.com/AdityaVN5/NewsGuard-AI/blob/main/Screenshots/vlcsnap-2025-04-01-21h49m20s470.png)
![](https://github.com/AdityaVN5/NewsGuard-AI/blob/main/Screenshots/Screenshot%202025-04-01%20211939.png)

## Usage

1.  **Enter News Claims:** In the Gradio interface, input the news claims you want to verify in the text box. Separate multiple claims with semicolons (;).
2.  **Analyze Credibility:** Click the "Analyze Credibility" button.
3.  **View Results:** The analysis results will be displayed in the output panel, including the credibility status, confidence score, and supporting evidence.
4.  **Red Alerts:** If a claim is contradicted, a red alert message will be shown.

## Code Overview

* `app.py`: Contains the main application code, including web scraping, credibility assessment, and the Gradio interface.
* `minicheck/`:  Directory containing the MiniCheck library for AI-powered fact-checking.

### Key Functions

* `search_web(query)`:  Performs web searches
* `parse_duckduckgo_results(html_content)`:  Parses the HTML content of the search results.
* `search_trusted_sources(query)`: Searches for information from trusted sources on the web.
* `assess_credibility(claim, snippets)`: Assesses the credibility of a claim using MiniCheck.
* `verify_news(text)`:  Orchestrates the claim verification process, including searching for information and assessing credibility. 
* `format_results(results)`: Formats the output for display in the Gradio interface. 
## Dependencies

* gradio
* minicheck
* requests
* fake-useragent
* beautifulsoup4
* nltk

## Troubleshooting

* **CAPTCHA Issues:** The script uses DuckDuckGo to minimize CAPTCHA challenges. However, if you encounter CAPTCHAs, try increasing the `RATE_LIMIT` or using a proxy list.
* **Model Loading Errors:** Ensure that the MiniCheck model is loaded correctly. Check the console output for any error messages related to model initialization.
* **Web Scraping Errors:** If you experience issues with web scraping, verify your internet connection and check for any changes in the structure of the DuckDuckGo search results page.
* **Gradio Interface Issues:** If the Gradio interface is not working as expected, ensure that all dependencies are installed correctly and that you are running the app.py file.

## Disclaimer

This tool provides credibility assessments based on AI analysis and web search results. It is essential to use this tool as a guide and not as a definitive source of truth. Always cross-reference information with multiple reliable sources before making decisions based on the analyzed claims.

## License

This project is licensed under the MIT License.

## Author

AdityaVN5

## Acknowledgements

* The MiniCheck library for providing the AI-powered fact-checking model.
* The developers of the Gradio library for the user-friendly interface.
* DuckDuckGo for providing a search engine that helps minimize CAPTCHA issues.
