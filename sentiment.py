"""
INFO 290 - FlickOh Project
Usage
"""

import codecs
import glob
import json
import os
import re
import time
import sys
import urllib
import urllib2

class Sentiment():
    
    movie = Movie()
    
    @staticmethod
    def get_sentiment(filename):
        """ Get sentiment analysis of tweets in the specified file

        This function utilizes the sentiment140 API.

        @param filename - the file is assumed to be in the json format and
        the first line will be discarded ({ "data" : [\n')
        and each tweet must be in a separate line. 
        """

        MAX_ITEMS = 8000               
        infile = codecs.open(filename, 'r', 'utf8', 'replace')
        infile.readline()  # discard the header
        
        out = open('sentiment_of_'+filename.split('/')[-1], 'w')
        out.write('{ "data" : [\n')
        reached_EOF = False

        while (not reached_EOF):               
            first = True
            count = 0
            POST_data = ''
            orig_text = {}
            while (count < MAX_ITEMS):            
                tweet = infile.readline()
                if (not tweet):             
                    reached_EOF = True
                    break
                tweet, original_text, tw_id = Sentiment.__extract_text(tweet)
                orig_text[tw_id] = original_text
                if (tweet == ''): continue
                if (first):
                    POST_data = '{ "data" : [\n' + tweet            
                    first = False
                else :
                    POST_data = POST_data + ',\n' + tweet
                count += 1
            
            if (POST_data == ''): continue
            POST_data = POST_data + ']}'

            # try to replace shortened text with original text here
            results = Sentiment.__connect_API(POST_data)
            Sentiment.__restore_orig_texts(results, orig_text)
            print(len(results['data']))            
            for item in results['data'][:-1]:
                out.write(json.dumps(item) +',\n')               
            out.write(json.dumps(results['data'][-1]))
            
            if (reached_EOF): out.write(']}\n')
            else : out.write(',\n')

            orig_text = {}
                    
        print("done")
        infile.close()
        out.close()

    @staticmethod
    def __connect_API(POST_data):
        API_URI = "http://www.sentiment140.com/api/bulkClassifyJson"
        req = urllib2.Request(API_URI, POST_data)
        response = urllib2.urlopen(req)
        results = response.read()
        return json.loads(results)

    @staticmethod
    def __restore_orig_texts(data, orig_text):
        for item in data['data']:
            item['text'] = orig_text[item['id']]
    
    @classmethod
    def __extract_text(cls, fulltweet):
        """Converts a full tweet to a format suitable for sentiment API.
        
        Take a full tweet (a line from the tweet file which ends with
        either ',\n' or ']}\n') and return a shoter tweet with only necessary
        fields. Also in the text field, replace
        any URL with <URL>, hashtag with <HT>, user_mentions with <UM>.
        This is to prevent these items from biasing the sentiment analysis.
        """
        
        data = {}
        try:
            if (fulltweet.find(',\n') != -1):
                data = json.loads(fulltweet[:-2])
            else :
                data = json.loads(fulltweet[:-3])
        except ValueError:
            data = json.loads(fulltweet[:-2])
        #else:
            #print(repr(fulltweet))

        newtext = data['text']            

        newtext = re.sub('#([^\s]*) ' , '<HT> ', newtext)
        newtext = re.sub('@([^\s]*) ' , '<UM> ', newtext)
        newtext = re.sub('http:\/\/([^\s]*) ' , '<URL> ', newtext)

        newtext = re.sub("[^a-zA-Z0-9<>\\s]", "", newtext)
        ntweet = {}
        ntweet['no'] = data['no']
        ntweet['id'] = data['id']
        ntweet['text'] = newtext
        ntweet['query'] = cls.movie.get_title(int(data['no']))
        ntweet['user'] = data['user']['screen_name']
        ntweet['created_at'] = data['created_at']
        ntweet['retweet_count'] = data['retweet_count']

        return (json.dumps(ntweet), data['text'], data['id'])

    @staticmethod
    def process_sentiment(directory, include_tweets=False):
        """Summarize the sentiment polarity for each movie from the files in the
        specified directory.

        This method will process all the files with extension .json
        in the given directory and will count the total number of tweets
        with negative, neutral, positive sentiments for each movie.
        """
        movie = Movie()
        NUM_MOVIES = movie.get_num_movies()
        
        def process(file_, polarity, texts):
            infile = open(file_, 'r')
            data = json.loads(infile.read())
            data = data['data']

            polarity_level = {0:"negative", 2:"neutral", 4:"positive"}

            for item in data:
                # "Mon Oct 29 06:15:21 +0000 2012"
                #time_ = time.strptime(item['created_at'],
                #                     "%a %b %d %I:%M:%S %z %Y")                
                polarity[item['no']][item['polarity']//2] += 1
                texts[item['no']][polarity_level[item['polarity']]] += [{"text":item['text']}]
                                
        stm_polarity = {}
        stm_texts = {}
        for i in range(0, NUM_MOVIES):
            stm_polarity[i] = [0,0,0]  # {datetime:[neg, neu, pos]}
            stm_texts[i] = {"negative":[], "neutral":[], "positive":[]}
            
        os.chdir(directory)
        for file_ in os.listdir("."):
            if file_.endswith(".json"): 
                process(file_, stm_polarity, stm_texts)

        os.mkdir('results')
        os.chdir('./results/')
        fw = open('sentiment_polarity_summary', 'w')
        fw.write("No,Title,#Neg,#Neu,#Pos,Total#\n")
        for key, value in stm_polarity.items():
            fw.write(str(key)+','+movie.get_title([key])+','+str(value[0])+','+
                     str(value[1])+','+str(value[2])+','+str(sum(value))+'\n')       
        fw.close()

        if (not include_tweets): return
        for i in range(0, NUM_MOVIES):            
            fw = open('sentiment_texts_' + str(i) + '.json', 'w')
            fw.write(json.dumps(stm_texts[i], indent=4))
            fw.close()        

                                                       
def Movie():
    
    @classmethod
    def get_title(cls, no):
        return cls.movies[no]

    @classmethod
    def get_num_movies(cls):
        return len(cls.movies)
    
    movies = {  0:"Frankenweenie",
                1:"Butter",
                2:"Taken 2",
                3:"The House I Live In",
                4:"The Paperboy",
                5:"V/H/S",
                6:"Argo",
                7:"Atlas Shrugged: Part 2",
                8:"Here Comes the Boom",
                9:"Seven Psychopaths",
                10:"Sinister",
                11:"Nobody Walks",
                12:"Smashed",
                13:"Pitch Perfect",
                14:"War of the Buttons",
                15:"Holy Motors",
                16:"Alex Cross",
                17:"Paranormal Activity 4",
                18:"The First Time",
                19:"The Sessions",
                20:"Tai Chi 0",
                21:"Chasing Mavericks",
                22:"Cloud Atlas",
                23:"Fun Size",
                24:"Silent Hill: Revelation 3D",
                25:"Flight",
                26:"The Man with the Iron Fists",
                27:"Wreck-It Ralph",
                28:"The Bay",
                29:"The Details",
                30:"High Ground",
                31:"Jack and Diane",
                32:"A Late Quartet",
                33:"This Must Be the Place",
                34:"Skyfall",
                35:"The Comedy",
                36:"Nature Calls",
                37:"Silver Linings Playbook",
                38:"The Twilight Saga: Breaking Dawn - Part 2",
                39:"Anna Karenina",
                40:"Dangerous Liaisons",
                41:"Price Check",
                42:"Red Dawn",
                43:"Rise of the Guardians",
                44:"The Central Park Five",
                45:"Rust & Bone",
                46:"Killing Them Softly",
                47:"The Collection",
                48:"Playing for Keeps",
                49:"Deadfall",
                50:"Hyde Park on Hudson",
                51:"Lay the Favorite",
                52:"The Hobbit: An Unexpected Journey",
                53:"Save the Date",
                54:"The Guilt Trip",
                55:"Monsters Inc",
                56:"Amour",
                57:"Zero Dark Thirty",
                58:"Cirque Du Soleil: Worlds Away",
                59:"Jack Reacher",
                60:"This is 40",
                61:"The Impossible",
                62:"Not Fade Away",
                63:"On the Road",
                64:"Django Unchained",
                65:"Les Miserables",
                66:"Parental Guidance",
                67:"Promised Land",
                68:"Quartet",
                69:"Hotel Transylvania",
                70:"Lincoln",
                71:"Life of Pi",
                72:"Talaash",
                73:"The Perks of Being a Wallflower",
                74:"Kill Me Now",
                75:"Wagner & Me",
                76:"Looper",
                77:"The Odd Life of Timothy Green",
                78:"Son of Sardaar",
                79:"ParaNorman",
                80:"Universal Soldier: Day of Reckoning",
                81:"Any Day Now",
                82:"Jason Becker: Not Dead Yet",
                83:"Trashed",
                84:"West of Memphis",
                85:"Lore"}

