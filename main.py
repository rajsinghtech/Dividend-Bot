import json
import requests
from datetime import datetime
import tweepy
import time
import os

# Twitter API credentials
consumer_key = os.environ.get("TWITTER_CONSUMER_KEY")
consumer_secret = os.environ.get("TWITTER_CONSUMER_SECRET")
access_token = os.environ.get("TWITTER_ACCESS_TOKEN")
access_token_secret = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")

# Authenticate to Twitter
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

# Stock API credentials
api_key = os.environ.get("STOCK_API_KEY")

def storeConfig(variables):
    with open('config.json', 'w') as file:
        json.dump(variables, file)
        
def loadConfig():
    with open('config.json', 'r') as file:
        variables = json.load(file)
    return variables

def grab_data(ticker):
    url = "https://api.polygon.io/v3/reference/dividends?ticker={}&apiKey={}".format(ticker, api_key)
    r = requests.get(url=url)
    data = r.json()['results'][0]
    return data

def grab_price(ticker):
    url = "https://api.polygon.io/v2/aggs/ticker/{}/prev?unadjusted=true&apiKey={}".format(ticker, api_key)
    r = requests.get(url=url)
    data = r.json()['results'][0]
    return data['vw'] # Volume Weighted Price

# True == is change / False == no change
def compareChange(ticker):
    data = grab_data(ticker)
    data["currentDate"] = "1-1-1999"
    config = loadConfig()
    if ticker not in config:
        print("New ticker added: {}".format(ticker))
        config[ticker] = data
        storeConfig(config)
        return True
    elif config[ticker]['declaration_date'] == data['declaration_date']:
        print("No change to {}".format(ticker))
        return False
    else:
        print("Change to {}".format(ticker))
        config[ticker] = data
        storeConfig(config)
        return True
        
def tweet(message, watchTicker):
    print("Tweeting: {}".format(message))
    currentDate = datetime.now().date()
    config = loadConfig()
    if config[watchTicker]['currentDate'] == str(currentDate):
        print("Already tweeted today")
    else:
        api = tweepy.API(auth)
        api.update_status(message)
        print("Tweet posted")

def main():
    while True:
        for key, value in loadConfig().items():
            print("--------------------")
            watchTicker = key
            try:
                change = compareChange(watchTicker)
                price = grab_price(watchTicker)
            except Exception as e:
                print(e)
                break
            config = loadConfig()
            exDivDate = datetime.strptime(config[watchTicker]["ex_dividend_date"], "%Y-%m-%d").date()
            payDate = datetime.strptime(config[watchTicker]["pay_date"], "%Y-%m-%d").date()
            currentDate = datetime.now().date()
            
            divYield = (config[watchTicker]['cash_amount'] / price) * 100 * config[watchTicker]['frequency']
            divYield = "{:.2f}".format(divYield) + "%"
            
            if change == True:
                print("Declaration Date changed for {}".format(watchTicker))
                tweet("${} dividend has been declared for ${} on {}, current yield {}".format(watchTicker, str(config[watchTicker]['cash_amount']), str(config[watchTicker]['ex_dividend_date']), divYield), watchTicker)
            
            daysLeftToBuy = (exDivDate - currentDate).days
            daysLeftTillPay = (payDate - currentDate).days

            # print("Days left to buy: {}".format(daysLeftToBuy))
            # print("Days left till payday: {}".format(daysLeftTillPay))
            
            if daysLeftToBuy == 0:
                tweet("Today is the last day to buy ${} to get the dividend, current yield {}, payday is {}".format(watchTicker, divYield, str(config[watchTicker]['pay_date'])), watchTicker)
            elif daysLeftToBuy == 1:
                tweet("Tomorrow is the last day to buy ${} to get the dividend, current yield {}, payday is {}".format(watchTicker, divYield, str(config[watchTicker]['pay_date'])), watchTicker)
            elif daysLeftToBuy == 3:
                tweet("There are {} days left to buy ${} to get the dividend, current yield {}, payday is {}".format(daysLeftToBuy, watchTicker, divYield, str(config[watchTicker]['pay_date'])), watchTicker)
            else:
                print("Dividend has already passed for ${}".format(watchTicker))
                if daysLeftTillPay == 0:
                    tweet("Today is payday for ${}, current yield {}".format(watchTicker, divYield), watchTicker)
                elif daysLeftTillPay == 1:
                    tweet("Tomorrow is payday for ${}, current yield {}".format(watchTicker, divYield), watchTicker)
                else:
                    print("Payday has already passed for ${}".format(watchTicker))
            
            config[watchTicker]['currentDate'] = str(currentDate)
            storeConfig(config)
        print("Sleeping")
        print(str(currentDate))
        time.sleep(60*60)
if __name__ == '__main__':
    main()