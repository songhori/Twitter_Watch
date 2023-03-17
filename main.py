import snscrape.modules.twitter as sntwitter
import pandas as pd
from summarise import summarise
from collections import Counter
from flask import Flask, render_template, request
import json
from sentiment import sentiment_analyzer
from sentiment import check_polarity

app = Flask(__name__)

# users = ['alikarimi_ak8', 'elonmusk', 'BarackObama', 'taylorlorenz', 'cathiedwood', 'ylecun']
users = ['taylorlorenz', 'cathiedwood', 'ylecun']
until = "2023-03-16"
since = "2023-03-01"



def get_data(query):
    data = sntwitter.TwitterSearchScraper(query).get_items()
    df = pd.DataFrame(data, columns=['date', 'user', 'rawContent', 'id'])
    return df

def get_rdata(rquery):
    data = sntwitter.TwitterSearchScraper(rquery).get_items()
    rdf = pd.DataFrame(data, columns=['date', 'user', 'rawContent', 'inReplyToTweetId'])
    return rdf



df_tw = [get_data(f"(from:{user}) until:{until} since:{since} -filter:replies") for user in users]
df_rp = [get_rdata(f"(to:{user}) until:{until} since:{since}") for user in users]



Tweets = [df['rawContent'] for df in df_tw]
Replies = [df['rawContent'] for df in df_rp]
sentiment_tw = [tweet.apply(lambda x: sentiment_analyzer(x)) for tweet in Tweets]
sentiment_rp = [reply.apply(lambda x: sentiment_analyzer(x)) for reply in Replies]
whole_sentiment = [list(sentiments_tw) + list(sentiments_rp) for sentiments_tw, sentiments_rp in zip(sentiment_tw, sentiment_rp)]
mean_metric = [sum(d['metric'] for d in sentiments)/len(sentiments) for sentiments in whole_sentiment]
sentiment_decision = [f"Sentiment of the whole Account is {check_polarity(metric)} with metric {metric:.2f}" for metric in mean_metric]
str_sentiment_tw = [sentiment.to_string(index=False, header=False) for sentiment in sentiment_tw]
str_sentiment_rp = [sentiment.to_string(index=False, header=False) for sentiment in sentiment_rp]
userrow = [df['user'].apply(lambda x: x['username']) for df in df_rp]
active_user = [Counter(row).most_common(5) for row in userrow]
str_Tweets = ['\n'.join(list(tweet)) for tweet in Tweets]
str_Replies = ['\n'.join(list(reply)) for reply in Replies]
description = [summarise(tweet) for tweet in str_Tweets]




@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form['selected_value']
        user_index = users.index(username)

        # tweets:
        query = f"(from:{username}) since:{until} -filter:replies"
        newtweets = get_data(query)['rawContent']
        alltweets = '\n'.join(newtweets) + str_Tweets[user_index]

        # replies:
        rquery = f"(to:{username}) since:{until}"
        newreplies = get_rdata(rquery)['rawContent']
        allreplies = '\n'.join(newreplies) + str_Replies[user_index]

        return render_template('index.html',
                               tweets=alltweets,
                               replies=allreplies,
                               description=description[user_index],
                               tw_sentiment=str_sentiment_tw[user_index],
                               rp_sentiment=str_sentiment_rp[user_index],
                               sent_deci=sentiment_decision[user_index],
                               active=active_user[user_index])
    else:
       return render_template('index.html')




@app.route('/accounts/')
def get_accounts():
    return json.dumps(users)


@app.route('/accounts/<username>/tweets')
def tweet(username):
    query = f"(from:{username}) since:{until} -filter:replies"
    newtweets = get_data(query)['rawContent']
    alltweets = list(newtweets) + list(Tweets[users.index(username)])
    return json.dumps(alltweets)


@app.route('/accounts/<username>/audience')
def reply(username):
    rquery = f"(to:{username}) since:{until}"
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