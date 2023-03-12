import snscrape.modules.twitter as sntwitter
import pandas as pd
from summarise import summarise
from collections import Counter
from flask import Flask, render_template, request
import re
import json

app = Flask(__name__)

users = ['alikarimi_ak8', 'BarackObama', 'taylorlorenz', 'cathiedwood', 'ylecun']
# users = ['BarackObama', 'ylecun', 'taylorlorenz']
until = "2023-03-11"
since = "2023-03-10"


def clear_text(text):
  # Use re.sub() to replace all mentions with an empty string
  cleaned_text = re.sub(r'@[A-Za-z0-9]+', '@', text)
  cleaned_text = re.sub(r'http\S+|www\S+', 'http', cleaned_text)
  return cleaned_text


def get_Content(query):
  data = sntwitter.TwitterSearchScraper(query).get_items()
  # df = pd.DataFrame(data, columns=['date', 'user', 'rawContent', 'id'])
  df = pd.DataFrame(data, columns=['rawContent'])
  # Discription = df.loc[0,'user']['rawDescription']
  # print (Discription)
  # df['user'] = df['user'].apply(lambda x: x['users'])
  result = df['rawContent'].apply(lambda x: clear_text(x))
  result = '\n'.join(list(result))
  return result


def get_data(query):
  data = sntwitter.TwitterSearchScraper(query).get_items()
  df = pd.DataFrame(data, columns=['date', 'user', 'rawContent', 'id'])
  # Description = df.loc[0,'user']['rawDescription']
  df['user'] = df['user'].apply(lambda x: x['username'])
  return df


# Sentiment Analysis
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

Tweets = [""] * len(users)
Replies = [""] * len(users)
sentiment_tw = [""] * len(users)
sentiment_rp = [""] * len(users)
count = [""] * len(users)
for i in range(len(users)):
  query = "(from:" + users[i] + ") until:" + until + " since:" + since + " -filter:replies"
  Tweets[i] = get_Content(query)
  rquery = "(to:" + users[i] + ") until:" + until + " since:" + since
  Replies[i] = get_Content(rquery)
  sentiment_tw[i] = analyzer.polarity_scores(Tweets[i])
  sentiment_rp[i] = analyzer.polarity_scores(Replies[i])
  # print(sentiment_tw[2])
  rdf = get_data(rquery)
  count[i] = Counter(rdf['user']).most_common(5)




@app.route('/', methods=['GET', 'POST'])
def index():
  if request.method == 'POST':
    username = request.form['selected_value']
    # print(username)
    # tweets:
    query = "(from:" + username + ") since:" + until + " -filter:replies"
    newtweets = get_Content(query)
    alltweets = newtweets + Tweets[users.index(username)]

    # replies:
    rquery = "(to:" + username + ") since:" + until
    newreplies = get_Content(rquery)
    allreplies = newreplies + Replies[users.index(username)]
    # a = list(sentiment_rp[users.index(username)])
    # b = list(sentiment_tw[users.index(username)])
    return render_template('index.html',
                           tweets=alltweets,
                           replies=allreplies,
                           # description='\n'.join(summary),
                           description="",
                           sentiment=sentiment_rp,
                           counter=count[users.index(username)])

  else:
    return render_template('index.html', tweets="", replies="")


@app.route('/accounts/')
def get_accounts():
  # get list of accounts
  accounts = users
  # code to get accounts
  return json.dumps(accounts)


@app.route('/accounts/<username>/tweets')
def tweet(username):
  query = "(from:" + username + ") since:" + until + " -filter:replies"
  newtweets = get_Content(query)
  alltweets = newtweets + Tweets[users.index(username)]
  return json.dumps(alltweets)


@app.route('/accounts/<username>/audience')
def reply(username):
  rquery = "(to:" + username + ") since:" + until
  newreplies = get_Content(rquery)
  allreplies = newreplies + Replies[users.index(username)]
  return json.dumps(allreplies)


@app.route('/accounts/<username>/counter')
def mycount(username):
  rquery = "(to:" + username + ") since:" + since
  rdf = get_data(rquery)
  answer = Counter(rdf['user']).most_common(5)
  return answer


@app.route('/accounts/<username>/sentiment')
def sentiment(username):
  answer = json.dumps(sentiment_tw[users.index(username)])
  return answer


@app.route('/accounts/<username>/audience/sentiment')
def sentiment2(username):
  answer = json.dumps(sentiment_rp[users.index(username)])
  return answer


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=81)
