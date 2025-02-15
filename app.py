import streamlit as st
import pandas as pd
import google.generativeai as genai
import time
import altair as alt
import threading
import re  # Import the regex library

# API Key (Replace with your actual API Key - securely manage this!)
# API key loading and configuration
# API key loading and configuration
try:
    api_key = st.secrets["api_key"]
    genai.configure(api_key=api_key)
except KeyError:
    st.error("API Key not found in Streamlit Secrets.")
    st.stop()
except Exception as e:
    st.error(f"Error configuring API: {e}")
    st.stop()

# Model Configuration
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-exp",  # Or appropriate model
    generation_config=generation_config,
)

# Rate Limiter


class RateLimiter:
    def __init__(self, tokens, fill_rate):
        self.tokens = float(tokens)
        self.fill_rate = float(fill_rate)
        self.timestamp = time.monotonic()
        self.lock = threading.Lock()

    def consume(self, tokens=1):
        with self.lock:
            now = time.monotonic()
            self.tokens += (now - self.timestamp) * self.fill_rate
            if self.tokens > tokens:  # Corrected: Allow consumption up to 'tokens'
                self.tokens = tokens  # Corrected: Cap tokens at maximum
            self.timestamp = now
            if self.tokens >= tokens:  # Corrected: check if we have enough tokens *before* consuming
                self.tokens -= tokens
                return True
            else:
                sleep_time = tokens / self.fill_rate
                time.sleep(sleep_time)
                self.tokens -= tokens
                return True


# Initialize Rate Limiter (adjust values based on your API limits)
rate_limiter = RateLimiter(tokens=10, fill_rate=2)  # 10 requests, refills at 2 per second


# Chat Session (Define the prompt once)
@st.cache_resource  # Cache this to avoid recreating it on every rerun
def create_chat_session():
    return model.start_chat(
        history=[
            {
                "role": "user",
                "parts": [
                    """
                    ## Improved Prompt for Sentiment Analysis AI Model

                    **Task:** Analyze the sentiment expressed in the given text and classify it as positive, negative, or neutral. Provide a clear and concise explanation for your classification. Crucially, provide a sentiment score as a *number* between -1.0 and +1.0.

                    **Input:** [The text to be analyzed]

                    **Output Format:** Sentiment: [Sentiment Category] - Reason: [Explanation] - Score: [Sentiment Score]

                    **Sentiment Categories:**

                    *   **Positive:** Expresses favorable opinions, emotions, or attitudes. Examples include praise, appreciation, excitement, joy, and approval.
                    *   **Negative:** Expresses unfavorable opinions, emotions, or attitudes. Examples include criticism, disappointment, anger, sadness, and disapproval.
                    *   **Neutral:** Expresses neither positive nor negative sentiment. Examples include factual statements, objective descriptions, and information without emotional tone. Ambiguous or mixed sentiment should lean towards neutral unless one sentiment clearly outweighs the other.

                    **Reasoning Guidelines:**

                    *   The reason should clearly justify the chosen sentiment category.
                    *   Refer to specific words, phrases, or sentence structures in the input text that support your analysis.
                    *   Explain *why* those elements indicate the identified sentiment.
                    *   Avoid vague or generic explanations like "the text sounds positive." Be specific.
                    *   For neutral sentiment, explain why the text lacks clear positive or negative indicators.

                    **Example 1:**

                    **Input:** "The movie was absolutely fantastic! The acting was superb, and the plot was captivating from beginning to end. I highly recommend it."

                    **Output:** Sentiment: Positive - Reason: The text contains strong positive words like "fantastic," "superb," and "captivating." The phrase "highly recommend" explicitly expresses approval. These elements clearly indicate a positive sentiment towards the movie. - Score: 0.9

                    **Example 2:**

                    **Input:** "I was extremely disappointed with the service. The staff was rude and unhelpful, and my order was completely wrong. I will never go back."

                    **Output:** Sentiment: Negative - Reason: Words like "disappointed," "rude," and "unhelpful" express negative feelings. The statement "my order was completely wrong" indicates a negative experience. The phrase "I will never go back" reinforces the negative sentiment. - Score: -0.8

                    **Example 3:**

                    **Input:** "The meeting is scheduled for 3 PM tomorrow in conference room B."

                    **Output:** Sentiment: Neutral - Reason: The text provides factual information about a meeting. It does not contain any words or phrases that express positive or negative emotions or opinions. - Score: 0.0

                    **Example 4 (Ambiguous):** "The movie was long, but it had some interesting moments."

                    **Output:** Sentiment: Neutral - Reason: While "long" could be seen as slightly negative, it's balanced by "interesting moments," creating a mixed sentiment. Without more context, the overall sentiment leans towards neutral as neither positive nor negative clearly outweighs the other. - Score: 0.1

                    **Example 5 (Mixed but leaning):** "The movie started slow and I almost left, but the ending was surprisingly good. I'm glad I stayed."

                    **Output:** Sentiment: Positive - Reason: Although the initial part of the movie was perceived negatively ("started slow," "almost left"), the overall sentiment is positive due to the "surprisingly good" ending and the expression of gladness ("I'm glad I stayed"). The positive sentiment at the end outweighs the initial negativity. - Score: 0.6

                    **Important Considerations for Your Model:**

                    *   **Context:** Sentiment can be context-dependent. Consider providing context to your model if necessary.
                    *   **Sarcasm/Irony:** Train your model to recognize sarcasm and irony, which can invert the apparent sentiment.
                    *   **Negation:** Handle negation words (e.g., "not," "no," "never") correctly.
                    *   **Intensity:** Consider the intensity of sentiment (e.g., "good" vs. "amazing").
                    *   **Subjectivity:** Distinguish between subjective opinions and objective facts.

                    *IMPORTANT: The final line of your output *must* be in the format 'Score: [Sentiment Score]' where [Sentiment Score] is a *number* between -1.0 and 1.0. *No additional text should follow the score.* Do not add any parenthesis or quotes. Just the output.
                    """,
                ],
            },
            {
                "role": "model",
                "parts": [
                    "Understood. I will analyze sentiment according to your provided guidelines, strictly adhering to the specified output format, including providing a numerical sentiment score between -1.0 and 1.0 with no trailing text.",
                ],
            },
        ]
    )


chat_session = create_chat_session()  # Initialise chat session


# Styling: Dark Mode Toggle
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

dark_mode = st.checkbox("Dark Mode", value=st.session_state.dark_mode)

if dark_mode != st.session_state.dark_mode:
    st.session_state.dark_mode = dark_mode
    st.rerun()  # Rerun app to apply new settings.


if st.session_state.dark_mode:
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #262730; /* Dark background */
            color: #f0f2f6;          /* Light text */
        }
        .stTextInput > div > div > input {
            background-color: #4f4f4f !important;
            color: #f0f2f6 !important;
        }
        .stTextArea > div > div > textarea {
            background-color: #4f4f4f !important;
            color: #f0f2f6 !important;
        }
        .stButton>button {
            color: #262730;
            background-color: #BB86FC; /* Purple button */
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #f0f2f6; /* Light gray background */
            color: #262730;          /* Dark text */
        }
        .stTextInput > div > div > input {
            background-color: #d3d3d3 !important;
            color: #262730 !important;
        }
        .stTextArea > div > div > textarea {
            background-color: #d3d3d3 !important;
            color: #262730 !important;
        }
        .stButton>button {
            color: white;
            background-color: #4CAF50; /* Green button */
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# Sentiment Analysis Function
@st.cache_data(show_spinner=False)  # Add caching
def analyze_sentiment(text, context="", detect_sarcasm=False):
    """Analyzes the sentiment of a given text using the Gemini model."""

    # Apply rate limiting before sending request
    if not rate_limiter.consume():
        st.warning("Rate limit exceeded. Please wait a moment.")
        return "Error", "Rate limit exceeded.", 0.0

    try:
        if detect_sarcasm:
            prompt = f"Context: {context}\nAnalyze the following text for sentiment, paying close attention to potential sarcasm:\n{text}"
        else:
            prompt = f"Context: {context}\nAnalyze the following text for sentiment:\n{text}"

        response = chat_session.send_message(prompt)
        full_text = response.text.strip().replace('`', "")  # Save complete response

        # Extract the sentiment category, reason, and score using more robust regex
        sentiment_match = re.search(r"Sentiment:\s*(\w+)", full_text)
        reason_match = re.search(r"Reason:\s*(.*?)\s*-\s*Score:", full_text)
        score_match = re.search(r"Score:\s*([-+]?\d*\.\d+|\d+)", full_text)  # Handles integer scores too

        if sentiment_match and reason_match and score_match:
            sentiment_category = sentiment_match.group(1)
            reason = reason_match.group(1).strip()
            score_str = score_match.group(1)

            try:
                score = float(score_str)
                if not -1.0 <= score <= 1.0:
                    st.warning(f"Sentiment score '{score}' is out of range (-1.0 to 1.0). Setting to 0.0")
                    score = 0.0  # Reset score if out of range
            except ValueError as ve:
                st.warning(f"Could not parse sentiment score from: '{score_str}'. Returning default score. ValueError: {ve}")
                score = 0.0  # Default score if parsing fails
            except Exception as e:
                st.error(f"Unexpected error parsing score: {e}")
                score = 0.0  # Default score for unexpected errors
            return sentiment_category, reason, score
        else:
            st.warning(f"Unexpected response format. Returning default score. Full text: {full_text}")
            return "Error", "Could not extract sentiment, reason, and score.", 0.0
    except Exception as e:
        st.error(f"An error occurred during analysis: {e}")
        return "Error", f"An error occurred during analysis: {e}", 0.0


# Streamlit App
st.title("Sentiment Analysis App")
st.markdown("From text to emotion: explore sentiment analysis.")
st.markdown(
    "This app can analyze the sentiment of text. Enter text to analyze manually, or enter multiple sentences for bulk sentiment analysis. The chart displays the distribution of sentiments for bulk sentences entered above."
)

# Sentiment Sensitivity Slider
sentiment_sensitivity = st.slider(
    "Sentiment Sensitivity",
    min_value=0.0,
    max_value=1.0,
    value=0.5,
    step=0.1,
    help="Adjust the model's sensitivity. Higher values more likely to classify as positive/negative.",
)

# Context Input
context_input = st.text_area(
    "Context (Optional):", help="Provide additional context to help with sentiment analysis."
)

# Sarcasm Detection Toggle
detect_sarcasm = st.checkbox(
    "Detect Sarcasm", value=False, help="Tell the model to consider sarcasm."
)

# Input Text Area
text_input = st.text_area("Enter text to analyze:", "This is a great app!")


def titlecase(s):
    return s[0].upper() + s[1:].lower() if s else s


# Analyze Button
if st.button("Analyze Sentiment"):
    if text_input:
        with st.spinner("Analyzing..."):
            sentiment, reason, score = analyze_sentiment(
                text_input, context_input, detect_sarcasm
            )
            st.write(f"**Sentiment:** {titlecase(sentiment)}")
            st.write(f"**Reason:** {reason}")
            st.write(f"**Sentiment Score:** {score:.2f}")  # Format score
    else:
        st.warning("Please enter some text to analyze.")


# Bulk Analysis Feature
st.header("Bulk Sentiment Analysis")
bulk_input = st.text_area("Enter multiple sentences (one sentence per line):", "")


if st.button("Analyze Bulk Sentiments"):
    if bulk_input:
        sentences = [line.strip() for line in bulk_input.splitlines() if line.strip()]
        bulk_data = []
        progress_bar = st.progress(0)  # Initialize progress bar
        total_sentences = len(sentences)

        for i, sentence in enumerate(sentences):
            with st.spinner(f"Analyzing: {sentence}"):
                sentiment, reason, score = analyze_sentiment(
                    sentence, context_input, detect_sarcasm
                )  # Pass context
                # Only append if sentiment analysis was successful
                if sentiment != "Error":
                    bulk_data.append(
                        {
                            "Sentence": sentence,
                            "Sentiment": titlecase(sentiment),
                            "Reason": reason,
                            "Sentiment Score": score,
                        }
                    )
                else:
                    st.warning(f"Sentiment analysis failed for sentence: {sentence}")
                # time.sleep(4)  # Respect API limits - removed; rate limiter handles this

            progress_percent = (i + 1) / total_sentences
            progress_bar.progress(progress_percent)

        bulk_df = pd.DataFrame(bulk_data)

        if not bulk_df.empty:  # Chart only shows if dataframe is not empty.
             #Get Sample Sentences. Create a column of first sentence in each category
            bulk_df['Sample Sentence'] = bulk_df.groupby('Sentiment')['Sentence'].transform(lambda x: x.iloc[0])
            st.dataframe(bulk_df)

            # Sentiment Distribution Chart for Bulk Analysis
            st.header("Sentiment Distribution Chart (Bulk Analysis)")

            try:
                color_scale = alt.Scale(
                    domain=["Positive", "Neutral", "Negative"], range=["green", "gray", "red"]
                )  # accessible colors

                chart = alt.Chart(bulk_df).mark_bar().encode(
                    x="Sentiment",
                    y="count()",
                    color=alt.Color("Sentiment", scale=color_scale),  # add color
                    tooltip=[
                        alt.Tooltip("Sentiment", title="Sentiment"),  # Sentiment Category
                        alt.Tooltip("count()", title="Count"),  # Count
                        alt.Tooltip("Sample Sentence", title="Sample Sentence"),
                    ],
                ).interactive()
                st.altair_chart(chart, use_container_width=True)
            except Exception as e:
                st.error(f"Error generating chart: {e}")
        else:
            st.warning("No valid sentiment data to display.")
    else:
        st.warning("Please enter some sentences for bulk analysis.")

st.markdown("---")

st.markdown("© 2025 PeterSynaptic. All rights reserved")
