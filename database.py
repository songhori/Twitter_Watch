import snscrape.modules.twitter as sntwitter
import pandas as pd
from summarise import summarise
from sentiment import sentiment_analyzer, check_polarity
import redis

since = "2023-02-01"

r = redis.Redis(
  host='redis-17081.c299.asia-northeast1-1.gce.cloud.redislabs.com',
  port=17081,
  password='q9726o8N7dBNpYQLoEsAOvVehvW7q1cj',
  decode_responses=True)


def set_database(user):
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
    
    # print(r.lrange(f'{user}:Tweets', 0, -1))
    # print(r.get(f'{user}:str_allTweets'))
    # print(r.lrange(f'{user}:Tweets_id', 0, -1))
    # print(r.lrange(f'{user}:Tweets_date', 0, -1))
    # print(r.lrange(f'{user}:met_sentiment_tw', 0, -1))
    # print(r.lrange(f'{user}:pol_sentiment_tw', 0, -1))
    # print(r.get(f'{user}:description'))
    # print(r.lrange(f'{user}:Replies', 0, -1))
    # print(r.get(f'{user}:str_allReplies'))
    # print(r.lrange(f'{user}:Replies_id', 0, -1))
    # print(r.lrange(f'{user}:Replies_date', 0, -1))
    # print(r.lrange(f'{user}:Replies_toTweetID', 0, -1))
    # print(r.lrange(f'{user}:met_sentiment_rp', 0, -1))
    # print(r.lrange(f'{user}:pol_sentiment_rp', 0, -1))
    # print(r.lrange(f'{user}:Replies_username', 0, -1))
    # print(r.get(f'{user}:mean_metric'))

since_l = "2023-03-23"
def scrape_newtweets(user):
    query = f"(from:{user}) since:{since_l} -filter:replies"
    for tweet in sntwitter.TwitterSearchScraper(query).get_items():
        
        if not r.exists(f'{user}:tweetdata:{tweet.id}'):
            tweet_data = {
                'date': str(tweet.date),
                'username': tweet.user.username,
            }
            if any(value is None for value in tweet_data.values()):
                continue
            Sentiment = sentiment_analyzer(tweet.rawContent)

            r.hset(f'{user}:tweetdata:{tweet.id}', mapping={**tweet_data})
            r.rpush(f'{user}:tweet-content',tweet.rawContent)
            r.rpush(f'{user}:tweet-polarity',Sentiment['polarity'])
            r.rpush(f'{user}:tweet-metric',Sentiment['metric'])

    reply_query = f'to:{user} since:{since_l}'
    for reply in sntwitter.TwitterSearchScraper(reply_query).get_items():
        if not r.exists(f'{user}:replydata:{reply.id}'):
            reply_data = {
                'date': str(reply.date),
                'username': reply.user.username,
                'in_reply_to_tweet_id': reply.inReplyToTweetId,
            }
            if any(value is None for value in reply_data.values()):
                continue

            Sentiment = sentiment_analyzer(reply.rawContent)

            r.hset(f'{user}:replydata:{reply.id}', mapping={**reply_data})
            r.rpush(f'{user}:reply-content',reply.rawContent)
            r.rpush(f'{user}:reply-polarity',Sentiment['polarity'])
            r.rpush(f'{user}:reply-metric',Sentiment['metric'])
