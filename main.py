from collections import Counter
from flask import Flask, render_template, request, jsonify
import json
import redis
from sentiment import check_polarity
from database import set_database, update_database
import concurrent.futures
from flask_compress import Compress
from flask_apscheduler import APScheduler

app = Flask(__name__)
Compress(app)
scheduler = APScheduler()

users = [
    'alikarimi_ak8', 'BarackObama', 'taylorlorenz', 'cathiedwood', 'ylecun'
]

myhost = 'redis-17081.c299.asia-northeast1-1.gce.cloud.redislabs.com'
mypassword = 'q9726o8N7dBNpYQLoEsAOvVehvW7q1cj'
myport = 17081

r = redis.Redis(host=myhost,
                password=mypassword,
                port=myport,
                decode_responses=True)

# to erase and re write the database:
# r.flushdb()
# with concurrent.futures.ThreadPoolExecutor() as executor:
#     executor.map(set_database, users)

def scheduled_task():
    print('Updating database...')
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(update_database, users)

scheduler.add_job(id='scheduled_task', func=scheduled_task, trigger='interval', minutes=1)
scheduler.init_app(app)
scheduler.start()

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    user = request.form['selected_value']
    pipe = r.pipeline()
    pipe.get(f'{user}:str_allTweets')
    pipe.get(f'{user}:str_allReplies')
    pipe.get(f'{user}:description')
    pipe.lrange(f'{user}:pol_sentiment_tw', 0, -1)
    pipe.lrange(f'{user}:pol_sentiment_rp', 0, -1)
    pipe.get(f'{user}:mean_metric')
    pipe.lrange(f'{user}:Replies_username', 0, -1)
    results = pipe.execute()
    sent_deci = f'Sentiment of the whole Account is {check_polarity(float(results[5]))} with metric {float(results[5]):.2f}'
    active_counts = Counter(results[6]).most_common(5)
    active = [x[0] for x in active_counts]
    return jsonify({
        'tweets': results[0],
        'replies': results[1],
        'description': results[2],
        'tw_sentiment': '\n'.join(list(results[3])),
        'rp_sentiment': '\n'.join(list(results[4])),
        'sent_deci': sent_deci,
        'active': '\n'.join(active)
    })

@app.route('/accounts')
def get_accounts():
    return json.dumps(users)

@app.route('/tweets/<username>')
def tweet(username):
    tweets = r.lrange(f'{username}:Tweets', 0, -1)
    return json.dumps(tweets)

@app.route('/replies/<username>')
def reply(username):
    replies = r.lrange(f'{username}:Replies', 0, -1)
    return json.dumps(replies)

@app.route('/audience/<username>')
def audience(username):
    audience = r.lrange(f'{username}:Replies_username', 0, -1)
    return json.dumps(audience)

@app.route('/activeaudience/<username>')
def active_a(username):
    audience = r.lrange(f'{username}:Replies_username', 0, -1)
    active_audience = Counter(audience).most_common(5)
    return json.dumps(active_audience)

@app.route('/tweetsentiment/<username>')
def sentiment_t(username):
    tweet_sentiment = r.lrange(f'{username}:pol_sentiment_tw', 0, -1)
    return json.dumps(tweet_sentiment)

@app.route('/replysentiment/<username>')
def sentiment_r(username):
    reply_sentiment = r.lrange(f'{username}:pol_sentiment_rp', 0, -1)
    return json.dumps(reply_sentiment)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=81)