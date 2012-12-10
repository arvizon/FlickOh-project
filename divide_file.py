#!/usr/bin/python
"""
INFO 290 - FlickOh Project
Author: Natth
Sample Usage: python partition_file.py 2000000 'tweets_file'
"""

import json
import os
import sys
import codecs

def divide_response_file(num_items, filename):
    """Divide a large file containing tweets from the streaming API
    into smaller files, each containing num_items tweets.

    The program assumes that each tweet is stored on a separate line,
    so it just copies and pastes line by line. It alsu ensures that
    the outfile will have a valid JSON format by adding {}, []
    at the beginning and the end of file as needed.

    """
    
    part = 1;
    prefix = filename.split('.')[0]
    ff = codecs.open(filename, 'r', 'utf8', 'replace')
    os.mkdir('./'+prefix)
    break_while = False
    while (True):
        part_file = codecs.open(prefix+'/'+filename.split('.')[0]+'_part'+str(part)+".json",
                                'w', 'utf8', 'replace')
        part_file.write('{ "data" : [')
        ending = "\n"
        for i in range(num_items):
            temp = ff.readline()
            if (temp == None or len(temp)<4):
                break_while = True
                ##print 'part ' + str(part) + ' : ' + str(i) + ' items'
                break
            if (temp[0] == '{' and temp[-3:] == '},\n'):
                part_file.write(ending)
                ending = ",\n"
                part_file.write(temp[:-2])
                ff.readline()
            else :               
                break_while = True
                break
        print 'part ' + str(part) + ' : ' + str(i+1) + ' items'
        part_file.write(']}')
        part_file.close()
        part = part+1
        if (break_while): break
    ff.close()

def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1

if __name__ == '__main__':
    partition_response_file(int(sys.argv[1]), str(sys.argv[2]))
