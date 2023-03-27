import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize

def download_nltk_resources():
    try:
        stopwords.words('english')
    except LookupError:
        nltk.download('stopwords')

    try:
        sent_tokenize('test sentence')
    except LookupError:
        nltk.download('punkt')

download_nltk_resources()

from nltk.probability import FreqDist
from nltk.stem import PorterStemmer
from heapq import nlargest


stop_words = set(stopwords.words('english'))
stemmer = PorterStemmer()

def summarise(text):
    # tokenize the sentences and words in text
    sentences = sent_tokenize(text)
    words = word_tokenize(text)

    # remove stopwords and stem remaining words
    filtered_words = [stemmer.stem(w.lower()) for w in words if not w in stop_words]

    # calculate word frequency
    freq_dist = FreqDist(filtered_words)
    top_words = nlargest(2, freq_dist, key=freq_dist.get)

    # summarize the text with top sentences that contain the most important words
    summary = []
    for sentence in sentences:
        if any(word in sentence.lower() for word in top_words):
           summary.append(sentence)

    summary = '\n'.join(summary)
    return summary