"""
INFO 290 FlickOh Project
Author: Natth

"""

import codecs
import json
import networkx as nx
import math
import operator


def main():
    # how to call the function to find movie recommendations for @alsmola.
    recommendation().find_recommendation('alsmola_core3_statuses_with_sentiment.json',
                                         'alsmola_core3_nodes.txt',
                                         'alsmola_core3_directfriends.txt',
                                         'alsmola_core3_edgelist',
                                         'alsmola')

class recommendation():
    
    @classmethod
    def find_recommendation(cls, sentiment_filename,
                            nodelist_filename,
                            direct_friend_filename,
                            edgelist_filename,
                            the_user):
        """Find recommended movies for the_user using naive Bayers classifier model.

        @param
        sentiment_filename - a JSON file containing statuses with sentiment polarity
                             of users in the_user's k-core interest graph. Each status is
                             assumed to have the field 'polarity' whose values are 0(neg), 2(neu), 4(pos),
                             'text' (tweet text), 'user' (user's screen_name).
        nodelist_filename - a text file containing all the screen names of users (one per line) in
                            the user's k-core graph (including the user, his direct friends (DFs) and
                            indirect friends (IDFs).
        direct_friend_filename - a text file containing all the screen names of the user's DFs.
        edgelist_filename - a graph file in edgelist format which is used to construct
                            the user's k-core interest graph.
        the_user - the screen name of the user for whom we want to find movie recommendations.                        
        """
        
        
        NUM_MOVIES = 86
        DEGREE_THRESHOLD = 50
        LIKE = 0
        DISLIKE = 1

        df_list = []
        df2idx = {}
        idf2idx = {}
        
        file_ = open(direct_friend_filename, 'r')        
        count = 0
        for each in file_.readlines():
            temp = each.strip()
            df_list.append([temp, 0])
            df2idx[temp] = count
            count += 1
        num_df = count    
        file_.close()

        count = 0        
        file_ = open(nodelist_filename, 'r')
        for each in file_.readlines():
            user = each.strip()
            if (user in df2idx): continue               
            idf2idx[user] = count
            count += 1
        num_idf = count
        file_.close()

        # create a num_idf x num_df matrix populated w/ [0,1] in each cell
        train_mat = [[[0,1] for col in range(num_df)] for row in range(num_idf)]     

        ## fill out train_matrix
        graph_edges = nx.read_edgelist(path=edgelist_filename, delimiter='\t').edges()
        for edge in graph_edges:
            ## edge = (idf, df)
            if (edge[1] in df2idx and edge[0] not in df2idx):
                train_mat[idf2idx[edge[0]]][df2idx[edge[1]]] = [1, 0]
                df_list[df2idx[edge[1]]][1] += 1
        graph_edges = [] # clear memory

        ## update the row of the central user
        tuser_idx = idf2idx[the_user]
        num_like = 0
        for col in range(num_df):
            if (df_list[col][1] >= DEGREE_THRESHOLD):
                train_mat[tuser_idx][col] = [1,0]
                num_like += 1
            else :
                train_mat[tuser_idx][col] = [0,1]

        ## update prob(class = like)
        prob_class = 2*[0]
        prob_class[LIKE] = float(num_like)/float(num_df)
        prob_class[DISLIKE] = 1 - prob_class[LIKE] 

        ## update prob[feature index i][like/dislike][class  like/dislike]
        ##       = proprotoin of likes/dislike in row i (i.e.[1,0]) given class = like/dislike
        EPSILON = 0.0000000000000001
        prob = [[[EPSILON,EPSILON] for i in range(2)] for row in range(num_idf)]
        
        num_dislike = num_df - num_like
        CLASS_LIKE = FEATURE_LIKE = 0
        CLASS_DIS = FEATURE_DIS = 1
        
        for row in range(num_idf):
            if (row == tuser_idx): continue
            nll = sum([1 for j in range(num_df)
                       if train_mat[tuser_idx][j][LIKE] == 1 and train_mat[row][j][LIKE] == 1])
            prob[row][FEATURE_LIKE][CLASS_LIKE] = float(nll+1)/float(num_like+2)
            prob[row][FEATURE_DIS][CLASS_LIKE]  = float(num_like-nll+1)/float(num_like+2)

            nld = sum([1 for j in range(num_df)
                       if train_mat[tuser_idx][j][DISLIKE] == 1 and train_mat[row][j][LIKE] == 1])
            prob[row][FEATURE_LIKE][CLASS_DIS] = float(nld+1)/float(num_dislike+2)
            prob[row][FEATURE_DIS][CLASS_DIS] = float(num_dislike-nld+1)/float(num_dislike+2)

        train_mat = [] # clear memory


        ## update the prediction_mat
        pred_mat = [[[0,0] for col in range(NUM_MOVIES)] for row in range(num_idf)]

        sentiment = json.loads(codecs.open(sentiment_filename,
                                              'r', 'utf8', 'replace').read())
        for status in sentiment['data']:
            if (status['name'] in df2idx): continue
            if (status['polarity'] >= 2):
                pred_mat[idf2idx[status['name']]][status['no']][LIKE] = 1
            else : pred_mat[idf2idx[status['name']]][status['no']][DISLIKE] = 1

        ## compute the probabilities
        rec_list = {}
        for col in range(NUM_MOVIES):
            log_class_like = math.log(prob_class[LIKE])
            log_class_dis = math.log(prob_class[DISLIKE])
            for row in range(num_idf):
                # row 2*i
                if (pred_mat[row][col][LIKE] == 1): # 'like' is present
                    log_class_like += math.log(prob[row][FEATURE_LIKE][CLASS_LIKE])
                    log_class_dis += math.log(prob[row][FEATURE_LIKE][CLASS_DIS])
                else :
                    log_class_like += math.log(prob[row][FEATURE_DIS][CLASS_LIKE])
                    log_class_dis += math.log(prob[row][FEATURE_DIS][CLASS_DIS])
                    
                # row 2*i + 1
                if (pred_mat[row][col][DISLIKE] == 1):  # 'dislike' is present               
                    log_class_like += math.log(prob[row][FEATURE_DIS][CLASS_LIKE])
                    log_class_dis += math.log(prob[row][FEATURE_DIS][CLASS_DIS])
                else :
                    log_class_like += math.log(prob[row][FEATURE_LIKE][CLASS_LIKE])
                    log_class_dis += math.log(prob[row][FEATURE_LIKE][CLASS_DIS])
                    
            if (log_class_like > log_class_dis):
                rec_list[cls.movies[col]] = log_class_dis/log_class_like

        print "Recommended List"
        for each in reversed(sorted(rec_list.iteritems(), key=operator.itemgetter(1))):
            print "%s \t %0.5f" % (each[0], each[1])
            
                
                

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
                
            

if __name__ == '__main__':
    main() 
                


        
            
 

        
        
        


        
         

        
        
        
