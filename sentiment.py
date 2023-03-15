from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import re


def clear_text(text):
  # Use re.sub() to replace all mentions with an empty string
  cleaned_text = re.sub(r'@[A-Za-z0-9]+', '@', text)
  cleaned_text = re.sub(r'http\S+|www\S+', 'http', cleaned_text)
  return cleaned_text

def check_polarity(num):
    if num <= -.5:
        return 'Negative'
    elif num >= .5:
        return 'Positive'
    else:
        return 'Neutral'

def sentiment_analyzer(text):
  cleaned_text = clear_text(text)
  analyzer = SentimentIntensityAnalyzer()
  metric = analyzer.polarity_scores(cleaned_text)['compound']
  polarity = check_polarity(metric)
  result = {'polarity': polarity, 'metric':metric}
  return result