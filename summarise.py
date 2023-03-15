# summerise the tweet method:
# import necessary modules

import nltk
nltk.download('stopwords')
nltk.download('punkt')
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.probability import FreqDist
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from heapq import nlargest



def summarise(text):
  # tokenize the sentences and words in text
  sentences = sent_tokenize(text)
  words = word_tokenize(text)

  # remove stopwords and stem remaining words
  stop_words = set(stopwords.words('english'))
  filtered_words = [
    PorterStemmer().stem(w.lower()) for w in words if not w in stop_words]

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
