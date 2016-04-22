# Kristian Elset Boe
# Student nr: 767956

import os
import re
from itertools import groupby

# Builds a simple dictionary of positive and negative words and connects
# them to a score to be used to calculate sentiment
def build_sentiment_dictionary():
    sentiment_dictionary = {}

    # The files are taken from http://nealcaren.web.unc.edu/an-introduction-to-text-analysis-with-python-part-3/
    pos_file = open("positive.txt", "r")
    for word in pos_file:
        sentiment_dictionary[word[:-1]] = 1
    pos_file.close()

    neg_file = open("negative.txt", "r")
    for word in neg_file:
        sentiment_dictionary[word[:-1]] = -1
    neg_file.close()

    return sentiment_dictionary

###
# Titles and reviews are taken from
# Andrew L. Maas, Raymond E. Daly, Peter T. Pham, Dan Huang, Andrew Y. Ng, and
# Christopher Potts. (2011). Learning Word Vectors for Sentiment Analysis. The 49th
# Annual Meeting of the Association for Computational Linguistics (ACL 2011).
###

# Builds a set from all the movie titles for quick lookup, also removes the \n
def build_set_from_titles():
    titles = set()

    txt_file = open("film_titles.txt", "r")
    for title in txt_file:
        titles.add(title[:-1])

    return titles

# Builds a dictionary between review file nr and the text in it
def build_review_dict():
    revs = {}
    rev_files = os.listdir(os.getcwd() + "/revs")
    i = 0

    html = re.compile('<[^>]*>')  # Removes all HTML rests from the review
    for rev_f in rev_files:
        txt_file = open("revs/" + rev_f, "r")
        review_text = txt_file.read()
        review_text = re.sub(html, '', review_text)
        revs[rev_f[:-4]] = review_text
        txt_file.close()
        i += 1
#        if i > 20:  #Can be included to run tests on a smaller sample of
#            break    #All the reviews

    return revs

# Builds a dictionary between letters and their soudnex counterpart
def build_soundex_table():
    soundex_chart = ["aehiouwy", "bfpv", "cgjkqsxz", "dt", "l", "mn", "r"]
    soundex_table = {}

    for i in range(len(soundex_chart)):
        for letter in soundex_chart[i]:
            soundex_table[letter] = str(i)

    return soundex_table

# Builds a dictionary between the soundex version of a title and the normal one
def build_soundex_titles_dict(titles, table):
    soundex_titles = {}

    for title in titles:
        s_word = to_soundex(title, table)
        soundex_titles[s_word] = title

    return soundex_titles

#### Not used
# Builds a dictionary between the review file nr and the soundex review text
def build_soundex_reviews_dict(reviews, table):
    soundex_reviews = {}

    for review in reviews:
        review_text = reviews[review]
        soundex_reviews[review] = to_soundex(review_text, table)

    return soundex_reviews

###
# The main method in the script. Takes a dictionary of review_nr->review_text,
# a set of titles and a dcitionary of word -> -1 | +1
# prints rev_nr, ":", title, review_sentiment, review_sentiment_score
###
def match_review_to_movie(reviews, titles, sentiment_dictionary):
    # Sets up aditional data structures
    review_to_title = {}
    soundex_table = build_soundex_table()
    soundex_titles = build_soundex_titles_dict(titles, soundex_table)

    # Initialises counters
    titles_found = 0
    no_match = 0
    no_plausable_match = 0
    positives = 0
    negatives = 0
    neutrals = 0


    for rev_nr in reviews:
        # Find title
        review_text = reviews[rev_nr]
        possible_titles = generate_possible_titles(titles, review_text)
        review_to_title[rev_nr] = determine_title(review_text, possible_titles, soundex_titles, soundex_table)
        title = review_to_title[rev_nr]

        # Update counters
        if title == "No title found":
            no_match += 1
        elif title == "No title plausible enough":
            no_plausable_match += 1
        else:
            titles_found += 1

        # Analyze sentiment
        review_sentiment_score = get_review_sentiment(review_text, sentiment_dictionary)
        if review_sentiment_score > 1:
            review_sentiment = "Positive"
            positives += 1
        elif review_sentiment_score < -1:
            review_sentiment = "Negative"
            negatives += 1
        else:
            review_sentiment = "Neutral"
            neutrals += 1

        # Print formated output
        print rev_nr, ":", title , review_sentiment

    # Print statistics
    print "Titles found:", titles_found
    print "Movies with no match:", no_match
    print "Movies with no plausible match:", no_plausable_match
    print "Positives:", positives
    print "Negatives", negatives
    print "Neutrals", neutrals

###################################
#   Output when algorithm is run on the full set of all 10000 reviews.
#    Titles found: 6792
#    Movies with no match: 1835
#    Movies with no plausible match: 1373
#    Positives: 5684
#    Negatives 1940
#    Neutrals 2376
#
#   Precission: : The proportion of the retrieved matches that are correct.
#                 There is no way to guarantee the Precission score seeing as
#                 I won't read through all the reviews my algorithm
#                 found a matching title for.
#                 A smaller sample of 5:
#                 10017 : Love Me or Leave Me Positive - correct
#                 10055 : 3 Needles Neutral - false (shoulde be Death becomes her)
#                 10078 : Avatar Negative - false (should be unknown)
#                 10070 : Frankenstrom Positive - false (should be unknown)
#                 10052 : Death Becomes Her Positive - correct
#                 Shows only 2 out of 5 are correct thus giving a precission
#                 of 2/5 = 0.4 . Not exceptional, but not terrible
#
#
#   Recall: The proportion of the correct matches that are retrieved.
#           Once again we can't verify the results, but if we assume the
#           algorithm worked flawlessly we get a recall of
#           6792/10000 = 0.67 (titles_found/nr_reviews)
####################################

# Generate possible titles from a reivew text based on the set of all titles
def generate_possible_titles(titles, review_text):
    possible_titles = {}

    for title in titles:
        if title in review_text:
            possible_titles[title] = generate_score(title)

    return possible_titles

# Generate inital score for a title based on nr of words in the title
# and the general length of the title to weed out titles with few
# characters like "G" or "Jam"
def generate_score(title):
    nr_title_words = len(title.split(' '))
    score = (nr_title_words * 5) * len(title)

    return score


def determine_title(review_text, possible_titles, soundex_titles, table):
    # If no imediate titles from exact string search go directly to soundex matching
    if not possible_titles:
        soundex_matching(review_text, possible_titles, soundex_titles, table)

        # If there are still no possible matches return
        if not possible_titles:
            return "No title found"

        # Else return the title with the highest score
        return max_dict(possible_titles)

    # Augment scores of movies with special traits like appearing first or appearing most
    score_titles(review_text, possible_titles)

    # Evaluate a posible match
    possible_match = max_dict(possible_titles)

    # If the possible match's score does not reach a certain threshold, proceed to soundex matching
    if possible_titles[possible_match] < 25:
        soundex_matching(review_text, possible_titles, soundex_titles, table)

    # Evaluate a new posible match
    result = max_dict(possible_titles)

    # Check if score threshold is still not met
    if possible_titles[result] > 18:
        return result
    else:
        return "No title plausible enough"

# Augment scores of movies with special traits like appearing first or appearing most
def score_titles(review_text, possible_titles):
    tmf = title_mentioned_first(review_text, possible_titles) # Title mentioned first
    tmmf = title_mentioned_most_frequently(review_text, possible_titles) # Title mentioned most frequently
    if tmf:
        possible_titles[tmf] = possible_titles[tmf] + (len(tmf.split(' ')) * 2)
    if tmmf:
        possible_titles[tmmf] = possible_titles[tmmf] + (len(tmmf.split(' ')) * 4)

def title_mentioned_first(review_text, possible_titles):
    pos = {}

    for title in possible_titles:
        try:
            pos[title] = review_text.index(" "+title+" ") # The " " are used to combat short titles like "G" getting credit
            # Pitfall is that reviews written with "title" will be missed
        except:
            continue
    if pos:
        return min_dict(pos)
    else:
        return None

def title_mentioned_most_frequently(review_text, possible_titles):
    frequency = {}

    for title in possible_titles:
        nr_mentions = review_text.count(" "+title+" ")
        possible_titles[title] = possible_titles[title]*len((title.split(' '))) # Once again a big bonus to mulit word titles
        # Reason if a multi word title is mentioned more than once it's probably the right one
        frequency[title] = nr_mentions
    if frequency:
        return max_dict(frequency)
    else:
        return None

# The approximate string matching algorithm Soundex
def soundex_matching(review_text, possible_titles, soundex_titles, table):
    # Turn the review text into soundex
    soundex_review_text = to_soundex(review_text, table)
    # Generate possible soundex titles based on the soundex review text and the dictionary of all soundex titles
    possible_soundex_titles = generate_possible_titles(soundex_titles, soundex_review_text)

    # Augment scores of movies with special traits like appearing first or appearing most
    score_titles(soundex_review_text, possible_soundex_titles)

    # Turn the soundex titles into normal text so they can be matched
    # Uses the dictionary soundex_titles(soundex -> title)
    titles_found_by_soundex = [soundex_titles[s_title] for s_title in possible_soundex_titles if possible_soundex_titles[s_title] > 20]

    # Augments titles found by exact search if also found by soundex
    for title in possible_titles:
        if title in titles_found_by_soundex:
            possible_titles[title] += len(title.split(' ')) * 3

    # Gives titles only found by soundex a big boost
    for s_title in titles_found_by_soundex:
        if s_title not in possible_titles:
            possible_titles[s_title] = len(s_title.split(' '))*len(s_title) * 10


# Two help functions to return the key from a dictionary with the highest value
def max_dict(dictionary):
    return max(dictionary.keys(), key=(lambda key: dictionary[key]))

def min_dict(dictionary):
    return min(dictionary.keys(), key=(lambda key: dictionary[key]))

# Turns a sentence into a soundex sentence
def to_soundex(string, table):
    string_list = string.split(' ')
    soundex_list = []

    for word in string_list:
        soundex_list.append(word_to_soundex(word, table))

    return ' '.join(soundex_list)

# Turns a word into a soundex word
def word_to_soundex(word, table):
    init_sound = []

    if not word:
        return ""
    init_sound.append(word[0])
    for letter in word[1:]:
        init_sound.append(table.get(letter, ""))

    # Applies the soundex transformations
    soundex = [l for l, g in groupby(init_sound)]  # remove duplicates
    soundex = [l for l in soundex if l != "0"]  # remove 0s
    soundex = soundex[0:4]  # Truncate
    soundex = ''.join(soundex)

    return soundex

# Loops through the review text and and calculates a sentiment score based on
# nr of positive words - nr of negative words
def get_review_sentiment(review_text, sentiment_dictionary):
    score = 0

    for word in review_text.split(' '):
        score += sentiment_dictionary.get(word, 0)

    return score

# Builds nescesary datastructures from files
titles = build_set_from_titles()
reviews = build_review_dict()
sentiment_dictionary = build_sentiment_dictionary()
#soundex_reviews = build_soundex_reviews_dict(reviews, soundex_table)

# Runs the algorithm
match_review_to_movie(reviews, titles, sentiment_dictionary)
