import tweepy
import Twitter.unimelb.utils.APIKEYS as keys
import Twitter.unimelb.utils.process as process
import Twitter.unimelb.utils.export as export
from cloudant.client import CouchDB
import couchdb
import json
import time

users = set()
key_len = len(keys.key_list)

with open("sources/users/all-unique-users.txt") as f:
    for line in f:
        users.add(line)


class MyStreamListener(tweepy.StreamListener):
    def on_status(self, status):
        print(status.text)

    def on_data(self, data):
        """Called when raw data is received from connection.

            write the received data into a file
        """
        global users
        # todo: clean the tweet then store the data into couch db & local disk
        js = json.loads(process.process_json(json.loads(data)))
        try:
            # if js["covid_related"] == "True":  # set the doc id
            export.save_tweet(json.dumps(js), coviddb, covidsafedb, symptomdb)
            # else:
        except Exception as e:
            print(e)

        user_id = js["user"]["id_str"]
        if user_id not in users:
            users.add(user_id)
            date = time.strftime("%H")
            # write new user ids into a file, the file is named by the date of current day
            with open("new-user-" + date + ".txt", 'a') as out:
                out.write(str(user_id) + "\n")
                out.flush()
                print(len(users))
        return True


client = CouchDB("admin", "password", url='http://172.26.131.173:5984', connect=True)
mydb1 = "test-covid"
mydb2 = "test-covid-symptom"
mydb3 = "test-covid-covidsafe"

# create databases if not exist
export.create_db(mydb1, client)
export.create_db(mydb2, client)
export.create_db(mydb3, client)

# get databases
try:
    couch_server = couchdb.Server("http://admin:password@172.26.131.173:5984/")
    coviddb = export.get_db(mydb1, couch_server)
    covidsafedb = export.get_db(mydb2, couch_server)
    symptomdb = export.get_db(mydb3, couch_server)
except Exception as e:
    print('Connection unsuccessful')
    print(e)

api = keys.get_api(keys.key_list, 19)

myStreamListener = MyStreamListener()
myStream = tweepy.Stream(auth=api.auth, listener=myStreamListener)

# add a filter to collect tweets in Australia
myStream.filter(locations=[110.46, -44.02, 154.46, -11.695])
