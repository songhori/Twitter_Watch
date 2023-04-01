import snscrape.modules.twitter as sntwitter
import pandas as pd
from summarise import summarise
from sentiment import sentiment_analyzer, check_polarity
import redis
from datetime import datetime, timedelta

since = "2023-02-01"

myhost = 'redis-17081.c299.asia-northeast1-1.gce.cloud.redislabs.com'
mypassword = 'q9726o8N7dBNpYQLoEsAOvVehvW7q1cj'
myport = 17081

r = redis.Redis(
  host=myhost,
  password=mypassword,
  port=myport,
  decode_responses=True)

def set_database(user):

    # keys_to_delete = r.keys(f'{user}:*')
    # if len(keys_to_delete) > 0:
    #     r.delete(*keys_to_delete)
    
    query = f"(from:{user}) since:{since} -filter:replies"
    data = sntwitter.TwitterSearchScraper(query).get_items()
    df = pd.DataFrame(data, columns=['date', 'user', 'rawContent', 'id'])
    
    if df['rawContent'].empty:
       Tweets = [' ']
       str_allTweets = 'No tweets, or the page is private'
       Tweets_date = ['0']
       met_sentiment_tw = [0]
       pol_sentiment_tw = ['No tweets to calculate sentiment polarity']
       Tweets_id = [0]
       description = 'Nothing...'
    else:
       Tweets = df['rawContent']
       str_allTweets = '\n'.join(list(Tweets))
       Tweets_date = df['date'].dt.strftime('%Y-%m-%d').tolist()
       met_sentiment_tw = Tweets.apply(lambda x: sentiment_analyzer(x))
       pol_sentiment_tw = met_sentiment_tw.apply(lambda x: check_polarity(x))
       Tweets_id = df['id']
       description = summarise(str_allTweets)
    
    rquery = f"(to:{user}) since:{since}"
    rdata = sntwitter.TwitterSearchScraper(rquery).get_items()
    rdf = pd.DataFrame(rdata, columns=['date', 'user', 'rawContent', 'id', 'inReplyToTweetId'])
    Replies = rdf['rawContent']
    str_allReplies = '\n'.join(list(Replies))
    Replies_id = rdf['id']
    Replies_date = rdf['date'].dt.strftime('%Y-%m-%d').tolist()
    Replies_toTweetID = rdf['inReplyToTweetId']
    Replies_username = rdf['user'].apply(lambda x: x['username']) 
    met_sentiment_rp = Replies.apply(lambda x: sentiment_analyzer(x))
    pol_sentiment_rp = met_sentiment_rp.apply(lambda x: check_polarity(x))
    
    whole_metric = list(met_sentiment_tw) + list(met_sentiment_rp)
    mean_metric = sum(whole_metric)/len(whole_metric) 
  
    pipe0 = r.pipeline()
    pipe0.rpush(f'{user}:Tweets', *Tweets)
    pipe0.set(f'{user}:str_allTweets', str_allTweets)
    pipe0.rpush(f'{user}:Tweets_id', *Tweets_id)
    pipe0.rpush(f'{user}:Tweets_date', *Tweets_date)
    pipe0.rpush(f'{user}:met_sentiment_tw', *met_sentiment_tw)
    pipe0.rpush(f'{user}:pol_sentiment_tw', *pol_sentiment_tw)
    pipe0.set(f'{user}:description', description)
    pipe0.rpush(f'{user}:Replies', *Replies)
    pipe0.set(f'{user}:str_allReplies', str_allReplies)
    pipe0.rpush(f'{user}:Replies_id', *Replies_id)
    pipe0.rpush(f'{user}:Replies_date', *Replies_date)
    pipe0.rpush(f'{user}:Replies_toTweetID', *Replies_toTweetID)
    pipe0.rpush(f'{user}:met_sentiment_rp', *met_sentiment_rp)
    pipe0.rpush(f'{user}:pol_sentiment_rp', *pol_sentiment_rp)
    pipe0.rpush(f'{user}:Replies_username', *Replies_username)
    pipe0.set(f'{user}:mean_metric', mean_metric)
    pipe0.execute()
    print(f'Finished creating database for {user}')

yesterday = datetime.now() - timedelta(days=1)
yesterday = yesterday.strftime('%Y-%m-%d')
def update_database(user):
    Tweets = []
    Tweets_id = []
    Tweets_date = []
    met_sentiments_tw = []
    pol_sentiments_tw = []
    query = f"(from:{user}) since:{yesterday} -filter:replies"
    old_Tweets_id = r.lrange(f'{user}:Tweets_id', 0, -1)
    for tweet in sntwitter.TwitterSearchScraper(query).get_items():
        if not str(tweet.id) in old_Tweets_id:
            Tweet = tweet.rawContent
            Tweets.append(Tweet)
            Tweet_id = tweet.id
            Tweets_id.append(Tweet_id)
            Tweet_date = tweet.date.strftime('%Y-%m-%d')
            Tweets_date.append(Tweet_date)
            met_sentiment_tw = sentiment_analyzer(Tweet)
            met_sentiments_tw.append(met_sentiment_tw)
            pol_sentiment_tw = check_polarity(met_sentiment_tw)
            pol_sentiments_tw.append(pol_sentiment_tw)
    
    if Tweets:
        oldTweets = r.lrange(f'{user}:Tweets', 0, -1)
        str_allTweets = '\n'.join(Tweets + oldTweets)
        description = summarise(str_allTweets)
        pipe = r.pipeline()
        pipe.lpush(f'{user}:Tweets', *Tweets[::-1])
        pipe.set(f'{user}:str_allTweets', str_allTweets)
        pipe.lpush(f'{user}:Tweets_id', *Tweets_id[::-1])
        pipe.lpush(f'{user}:Tweets_date', *Tweets_date[::-1])
        pipe.lpush(f'{user}:met_sentiment_tw', *met_sentiments_tw[::-1])
        pipe.lpush(f'{user}:pol_sentiment_tw', *pol_sentiments_tw[::-1])
        pipe.set(f'{user}:description', description)
        pipe.execute()
    
    Replies = []
    Replies_id = []
    Replies_date = []
    Replies_toTweetID = []
    Replies_username = []
    met_sentiments_rp = []
    pol_sentiments_rp = []
    rquery = f"(to:{user}) since:{yesterday}"
    old_Replies_id = r.lrange(f'{user}:Replies_id', 0, -1)
    for reply in sntwitter.TwitterSearchScraper(rquery).get_items():
        if not str(reply.id) in old_Replies_id:
            Reply = reply.rawContent
            Replies.append(Reply)
            Reply_id = reply.id
            Replies_id.append(Reply_id)
            Reply_date = reply.date.strftime('%Y-%m-%d')
            Replies_date.append(Reply_date)
            Reply_toTweetID = reply.inReplyToTweetId
            if not Reply_toTweetID:
                Reply_toTweetID = 0
            Replies_toTweetID.append(Reply_toTweetID)
            Reply_username = reply.user.username
            Replies_username.append(Reply_username)
            met_sentiment_rp = sentiment_analyzer(Reply)
            met_sentiments_rp.append(met_sentiment_rp)
            pol_sentiment_rp = check_polarity(met_sentiment_rp)
            pol_sentiments_rp.append(pol_sentiment_rp)
    
    if Replies:
        oldReplies = r.lrange(f'{user}:Replies', 0, -1)
        str_allReplies = '\n'.join(Replies + oldReplies)
        pipe = r.pipeline()
        pipe.lpush(f'{user}:Replies', *Replies[::-1])
        pipe.set(f'{user}:str_allReplies', str_allReplies)
        pipe.lpush(f'{user}:Replies_id', *Replies_id[::-1])
        pipe.lpush(f'{user}:Replies_date', *Replies_date[::-1])
        pipe.lpush(f'{user}:Replies_toTweetID', *Replies_toTweetID[::-1])
        pipe.lpush(f'{user}:met_sentiment_rp', *met_sentiments_rp[::-1])
        pipe.lpush(f'{user}:pol_sentiment_rp', *pol_sentiments_rp[::-1])
        pipe.lpush(f'{user}:Replies_username', *Replies_username[::-1])
        pipe.execute()
    
    met_sentiment_tw = r.lrange(f'{user}:met_sentiment_tw', 0, -1)
    met_sentiment_tw = [float(x) for x in met_sentiment_tw]
    met_sentiment_rp = r.lrange(f'{user}:met_sentiment_rp', 0, -1)
    met_sentiment_rp = [float(x) for x in met_sentiment_rp]
    whole_metric = met_sentiment_tw + met_sentiment_rp
    mean_metric = sum(whole_metric)/len(whole_metric) 
    r.set(f'{user}:mean_metric', mean_metric)
