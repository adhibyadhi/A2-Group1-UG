"""
COSC2671 Social Media and Network Analytics
@author Hexu Chen, RMIT University, 2026
@author Chenglong Ma, RMIT University, 2026

YouTube version (adapted from RedditProcessing.py)

Modified by Undergraduate (UG) Group 1 for Assignment 2: Choose Your Own Analysis
"""
import re

class YouTubeProcessing:
    """
    This class is used to pre-process YouTube video titles and comments.
    This centralises the processing to one location. Feel free to add or edit.

    Note: The core NLP logic is identical to RedditProcessing —
    tokenisation, stopword removal, and filtering are platform-agnostic.
    """
    def __init__(self, tokeniser=None, stopwords=None, stemmer=None):
        """
        Initialise the tokeniser and set of stopwords to use.

        @param tokeniser: NLTK tokeniser (e.g. TweetTokenizer)
        @param stopwords: list of stopwords to remove
        @param stemmer: NLTK stemmer (e.g. PorterStemmer)
        """
        self.tokeniser = tokeniser
        self.stopwords = set(stopwords) if stopwords is not None else set()
        self.stemmer = stemmer

    def clean_raw_text(self, text):
        """
        Perform the cleaning of raw text.
        @param text: the text (video title or comment) to process

        @returns: cleaned text
        """
        text = str(text)
        text = text.replace('\n', ' ')
        text = text.replace('\r', ' ')
        text = text.lower()

        """
        Additional regex cleaning steps:

        - Remove URLs
        - Remove common unicode punctuation
        - Remove extra whitespace
        """
        text = re.sub(r'http\S+|www\S+', '', text)
        text = re.sub(r'[\u2018\u2019\u201c\u201d\u2014]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def process(self, text):
        """
        Tokenise and clean text for NLP analysis.

        @param text: video title, description, comment, or reply text
        @returns: list of processed tokens
        """
        text = self.clean_raw_text(text)
        if self.tokeniser is not None:
            tokens = self.tokeniser.tokenize(text)
        else:
            tokens = text.split()

        processed_tokens = []
        for token in tokens:
            token = token.strip().lower()

            # Remove URLs, numbers, empty tokens, and stopwords
            if not token:
                continue
            if token in self.stopwords:
                continue
            if re.match(r'^http', token):
                continue
            if token.isdigit():
                continue

            # Remove tokens that contain no alphabetic characters
            if re.search(r'[a-zA-Z]', token) is None:
                continue
            if self.stemmer is not None:
                token = self.stemmer.stem(token)

            processed_tokens.append(token)

        return processed_tokens

    def joined_tokens(self, text):
        """
        Return processed text as a single string.

        This is useful for sklearn vectorisers, topic modelling,
        TF-IDF, and sentiment-analysis pipelines.

        @param text: raw text
        @returns: cleaned token string
        """
        return ' '.join(self.process(text))