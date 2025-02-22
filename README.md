# Sentiment Analysis App

## Overview

This Streamlit application performs sentiment analysis on text using the Google Gemini AI model. It allows users to analyze the sentiment of single text inputs or perform bulk analysis on multiple sentences. The app provides a sentiment classification (Positive, Negative, or Neutral), a reasoned explanation, and a sentiment score ranging from -1.0 to +1.0.

## Features

*   **Single Text Analysis:** Analyze the sentiment of a single text input.
*   **Bulk Sentiment Analysis:** Analyze the sentiment of multiple sentences provided as a list (one sentence per line).
*   **Sentiment Sensitivity Adjustment:** Adjust the model's sensitivity to fine-tune the classification.
*   **Contextual Input:** Provide additional context to improve the accuracy of sentiment analysis.
*   **Sentiment Distribution Chart:** Visualize the distribution of sentiments for bulk analysis using an interactive Altair chart.
*   **Rate Limiting:** Implements rate limiting to adhere to API usage restrictions.
*   **Clear Output:** Provides the sentiment, reason, and score in an easy-to-understand format.

## Technologies Used

*   **Streamlit:** For building the interactive web application.
*   **Pandas:** For data manipulation and analysis (primarily for bulk analysis).
*   **Google Generative AI (Gemini):** For performing the sentiment analysis.
*   **Altair:** For creating the sentiment distribution chart.
*   **Python:** The primary programming language.
*   **Regex (re):** For extracting data from model output.

## Setup and Installation

1.  **Prerequisites:**
    *   Python 3.7+
    *   A Google Cloud project with the Gemini API enabled.
    *   A Google API key with access to the Gemini API.

2.  **Install Dependencies:**

    ```bash
    pip install streamlit pandas google-generativeai altair
    ```

3.  **Set up API Key:**

    *   The application uses Streamlit Secrets to securely manage the API key.
    *   Create a `.streamlit/secrets.toml` file in your project directory.
    *   Add your API key to the file:

        ```toml
        api_key = "YOUR_API_KEY"
        ```

    **Important:** Never hardcode your API key directly in the code.  Always use environment variables or a secrets management system.

4.  **Run the Application:**

    ```bash
    streamlit run your_app_name.py  # Replace your_app_name.py with the actual filename
    ```

    This will start the Streamlit application in your web browser.

## Code Structure

The code is organized into the following main sections:

*   **Import Libraries:** Imports necessary libraries.
*   **API Key Configuration:** Loads and configures the Google Gemini API key.
*   **Model Configuration:** Configures the Gemini model parameters (temperature, top\_p, etc.).
*   **Rate Limiter:** Implements a `RateLimiter` class to control the rate of API requests.
    *   The `RateLimiter` class uses a token bucket algorithm to limit the number of requests sent to the Gemini API within a specific time frame.
    *   The `consume()` method checks if enough tokens are available before sending a request. If not, it waits until enough tokens are replenished.
*   **Chat Session Initialization:** Creates a chat session with the Gemini model.
    *   Uses `st.cache_resource` to cache the chat session and prevent re-initialization on every rerun.
    *   Includes a detailed prompt in the initial chat history to guide the model's sentiment analysis.  This prompt defines the task, input/output formats, sentiment categories, reasoning guidelines, and examples.
*   **Styling (Dark Mode):** Implements a dark mode toggle using Streamlit's `st.session_state` and custom CSS.
*   **`analyze_sentiment()` Function:** This is the core function that performs sentiment analysis.
    *   It takes text and optional context as input.
    *   It uses the Gemini model to analyze the sentiment.
    *   It extracts the sentiment category, reason, and score from the model's response using regular expressions.
    *   It includes error handling and validation to ensure the score is within the valid range (-1.0 to 1.0).
    *   It uses `st.cache_data` for caching, improving performance.
    *   It also calls the rate limiter before sending the request to the API
*   **Streamlit UI:**
    *   Defines the structure and elements of the Streamlit application, including:
        *   Title and description
        *   Sentiment sensitivity slider
        *   Context input area
        *   Text input area
        *   Analyze button
        *   Bulk sentiment analysis section
        *   Sentiment distribution chart
*   **Bulk Analysis:** Allows analyzing multiple sentences at once.
    *   Splits the input text into sentences.
    *   Iterates through the sentences, calling `analyze_sentiment()` for each.
    *   Displays the results in a Pandas DataFrame.
    *   Generates a sentiment distribution chart using Altair.
*   **Helper Functions:**
    *   `titlecase()`: Converts a string to title case.

## Using the Application

1.  **Enter Text:** In the "Enter text to analyze" text area, type or paste the text you want to analyze.
2.  **Adjust Sensitivity (Optional):** Use the "Sentiment Sensitivity" slider to adjust the model's sensitivity. Higher values make the model more likely to classify sentiments as strongly positive or negative.
3.  **Provide Context (Optional):** In the "Context (Optional)" text area, provide any additional context that might help the model understand the sentiment.
4.  **Click "Analyze Sentiment":** The app will display the sentiment, reason, and score.
5.  **Bulk Analysis:**
    *   Enter multiple sentences in the "Enter multiple sentences" text area (one sentence per line).
    *   Click "Analyze Bulk Sentiments".
    *   The app will display a table with the results for each sentence and a sentiment distribution chart.

## Rate Limiting

To prevent abuse and ensure fair usage of the Gemini API, the application implements rate limiting. The `RateLimiter` class limits the number of requests that can be sent to the API within a specific time frame. If you exceed the rate limit, the application will display a warning message.

## Error Handling

The application includes error handling to gracefully handle potential issues, such as:

*   Invalid API key
*   API request failures
*   Unexpected response formats
*   Sentiment score out of range

Error messages are displayed in the Streamlit UI to inform the user of any problems.

## Future Enhancements

*   **Improved Sarcasm Detection:** Implement more robust sarcasm detection.
*   **Language Detection:** Automatically detect the language of the input text.
*   **More Advanced Visualization:**  Explore more sophisticated visualization techniques.
*   **User Authentication:** Add user authentication for personalized settings and usage tracking.

## Author

PeterSynaptic
