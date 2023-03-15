import snscrape.modules.twitter as sntwitter
import pandas as pd
from summarise import summarise
from collections import Counter
from flask import Flask, render_template, request
import json
from sentiment import sentiment_analyzer

app = Flask(__name__)

# users = ['alikarimi_ak8', 'elonmusk', 'BarackObama', 'taylorlorenz', 'cathiedwood', 'ylecun']
users = ['taylorlorenz', 'cathiedwood', 'ylecun']
until = "2023-03-14"
since = "2023-02-01"


def get_data(query):
    data = sntwitter.TwitterSearchScraper(query).get_items()
    df = pd.DataFrame(data, columns=['date', 'user', 'rawContent', 'id'])
    return df


def get_rdata(rquery):
    data = sntwitter.TwitterSearchScraper(rquery).get_items()
    rdf = pd.DataFrame(data, columns=['date', 'user', 'rawContent', 'inReplyToTweetId'])
    return rdf


df_tw = [""] * len(users)
df_rp = [""] * len(users)
for i in range(len(users)):
    query = "(from:" + users[i] + ") until:" + until + " since:" + since + " -filter:replies"
    rquery = "(to:" + users[i] + ") until:" + until + " since:" + since
    df_tw[i] = get_data(query)  #tweet dataframe
    df_rp[i] = get_rdata(rquery)  #reply dataframe


Tweets = [""] * len(users)
Replies = [""] * len(users)
sentiment_tw = [""] * len(users)
sentiment_rp = [""] * len(users)
active_user = [""] * len(users)
description = [""] * len(users)
str_Tweets = [""] * len(users)
str_Replies = [""] * len(users)
str_sentiment_tw = [""] * len(users)
str_sentiment_rp = [""] * len(users)
userrow = [""] * len(users)
for i in range(len(users)):
    Tweets[i] = df_tw[i]['rawContent']
    Replies[i] = df_rp[i]['rawContent']
    sentiment_tw[i] = Tweets[i].apply(lambda x: sentiment_analyzer(x))
    sentiment_rp[i] = Replies[i].apply(lambda x: sentiment_analyzer(x))
    str_sentiment_tw[i] = sentiment_tw[i].to_string(index=False, header=False)
    str_sentiment_rp[i] = sentiment_rp[i].to_string(index=False, header=False)
    userrow[i] = df_rp[i]['user'].apply(lambda x: x['username'])
    active_user[i] = Counter(userrow[i]).most_common(5)
    str_Tweets[i] = '\n'.join(list(Tweets[i]))
    str_Replies[i] = '\n'.join(list(Replies[i]))
    description[i] = summarise(str_Tweets[i])


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
       username = request.form['selected_value']
  
       # tweets:
       query = "(from:" + username + ") since:" + until + " -filter:replies"
       newtweets = get_data(query)['rawContent']
       newstr_Tweets = '\n'.join(list(newtweets))
       alltweets = newstr_Tweets + str_Tweets[users.index(username)]
  
       # replies:
       rquery = "(to:" + username + ") since:" + until
       newreplies = get_rdata(rquery)['rawContent']
       newstr_Replies = '\n'.join(list(newreplies))
       allreplies = newstr_Replies + str_Replies[users.index(username)]
       return render_template('index.html',
                              tweets=alltweets,
                              replies=allreplies,
                              description=description[users.index(username)],
                              tw_sentiment=str_sentiment_tw[users.index(username)],
                              rp_sentiment=str_sentiment_rp[users.index(username)],
                              active=active_user[users.index(username)])
  
    else:
       return render_template('index.html')


@app.route('/accounts/')
def get_accounts():
    return json.dumps(users)


@app.route('/accounts/<username>/tweets')
def tweet(username):
    query = "(from:" + username + ") since:" + until + " -filter:replies"
    newtweets = get_data(query)['rawContent']
    alltweets = list(newtweets) + list(Tweets[users.index(username)])
    return json.dumps(alltweets)


@app.route('/accounts/<username>/audience')
def reply(username):
    rquery = "(to:" + username + ") since:" + until
    newreplies = get_rdata(rquery)['rawContent']
    allreplies = list(newreplies) + list(Replies[users.index(username)])
    return json.dumps(allreplies)


@app.route('/accounts/<username>/counter')
def mycount(username):
    answer = active_user[users.index(username)]
    return answer


@app.route('/accounts/<username>/sentiment')
def sentiment(username):
    answer = json.dumps(list(sentiment_tw[users.index(username)]))
    return answer


@app.route('/accounts/<username>/audience/sentiment')
def sentiment2(username):
    answer = json.dumps(list(sentiment_rp[users.index(username)]))
    return answer


if __name__ == '__main__':
   app.run(host='0.0.0.0', port=81)
