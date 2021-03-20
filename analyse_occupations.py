from prompt_toolkit import print_formatted_text
from prompt_toolkit import HTML
from time import time
import pandas as pd
import pickle
import os
import re


# This script is used to process the data obtained from the zodiac script to download
# data from wikipedia. It works by extracting every word of every summary, counting
# the number of their occurrences and then sorting them accordingly.
# Since the first sentence of the summary has, beside other things, the occupation
# of a person, these will rank quite high in the number of occurrences, and thus
# it is possible to get a comprehensive list of every possible job.

# Of course there will be other words in this list as well, so it is necessary to
# manually go through the list and sort the words in useful and useless lists.

# After the words are sorted, each summary is checked for an occurrence of a word
# on the list of occupations. If there is a hit, it can be assumed that the person
# has this occupation. It is then stored with the person, thus archiving a
# data-pair [zodiac, occupation].






# get character class. A gem I found at https://code.activestate.com/recipes/134892/ .
# This allows for the input to be captures directly after a button is hit, without
# the need to confirm the input with return. This will help immensly at going through
# the list of words later on, since there are several hundred to a few thousand words
# that need to be checked.
# This is the unix variatiant, if you are using Windows, just replace this class
# with the code in the link.

class _Getch:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


# Exception to break out of a nested loop.
class BreakIt(Exception): pass


# load list of useful and useless words

def load_lists(filepath="./zodiac_files/lists/"):

    getch = _Getch()
    print("Load lists? [y]es, [n]o")
    while True:
        decision = getch()
        if decision == "y":
            try:
                with open(filepath + "useless.txt", "rb") as fp:
                    useless = pickle.load(fp)
                with open(filepath + "useful.txt", "rb") as fp:
                    useful = pickle.load(fp)
                print("Lists loaded")

            except FileNotFoundError:
                print("Lists not found, using blank lists")
                useless = []
                useful = []
            break
        elif decision == "n":
            useless = []
            useful = []
            print("Blank Lists generated")
            break

    print()
    return useless, useful


# save lists of occupation
def save_lists(useless, useful, filepath="./zodiac_files/lists/"):

    getch = _Getch()
    print("\nSave files? [y]es, [n]o")
    while True:
        decision = getch()
        if decision == "y":
            pre = input("prefix?")
            filepath = filepath + pre
            with open(filepath + "useful.txt", "wb") as fp:
                pickle.dump(useful, fp)

            with open(filepath + "useless.txt", "wb") as fp:
                pickle.dump(useless, fp)
            break
        elif decision == "n":
            break


# load data downloaded with the zodiac script
def load_data():
    directory = r'./zodiac_files/data/'

    frame = pd.DataFrame()

    print("Loading data...\n")
    for file in os.listdir(directory):
        filepath = directory + file
        frame = frame.append(pd.read_csv(filepath, sep="$"))

    return frame


# reading out each word with its word count
def read_words(frame):

    print("Reading words...\n")
    word_dict = {}
    sentences = []

    for i, j in frame.iterrows():
        sentences.append(j['description'])

    for s in sentences:

        # strip punctuation of the sentences, since they would
        # generate unusable data. For example, "developer" and "developer."
        # would both be stored and treated as two different instances.
        try:
            valid = re.sub(r"[^A-Za-z]+", " ", s)
        except TypeError:
            continue
        words = valid.lower().split(" ")
        for word in words:
            if len(word) > 2:
                if not word in word_dict:
                    word_dict[word] = 1
                else:
                    word_dict[word] += 1

    # sort dictionary by value
    sorted_words = sorted(word_dict.items(), key=lambda kv: kv[1])[::-1]
    return sorted_words


# go through the extracted words and sort them into useful and useless.
def check_words(sorted_words):

    filepath = "./zodiac_files/lists/"
    useless, useful = load_lists(filepath)
    getch = _Getch()
    max = 0
    for word, occurences in sorted_words[0:200]:
        if len(word) > max:
            max = len(word)

    counter = 0
    last = []

    print("Evaluate words:")
    try:
        while counter < len(sorted_words):
            to_check = sorted_words[counter]
            is_new = True

            for word, n in useful:
                if word == to_check[0]:
                    del sorted_words[counter]
                    is_new = False

            for word, n in useless:
                if word == to_check[0]:
                    del sorted_words[counter]
                    is_new = False

            while is_new:
                to_print = to_check[0].ljust(max + 2) + "f: useless - j: useful - b: back - x: interrupt"
                print(to_print, end="\r")
                decision = getch()

                if decision == "j":
                    useful.append(to_check)
                    last.append(1)
                    to_print = "<ForestGreen>" + to_check[0].ljust(max + 2) + \
                               "</ForestGreen>f: useless - j: <ForestGreen>useful</ForestGreen> - b: back - x: interrupt"
                    break

                # there are some sports in the list, and since "football" or "soccer" could mean
                # different things based on context, with a button press on "s" these will get
                # changed into "football player", "soccer player" thus making it unambiguous.
                if decision == "s":
                    to_check = (to_check[0] + " player", to_check[1])
                    to_print = "<ForestGreen>Added as %s</ForestGreen>".ljust(100) % (to_check[0])
                    last.append(1)
                    useful.append(to_check)
                    break

                # same as the last case, but with a more general approach. I did not use it, but
                # here it is.
                if decision == "a":
                    addition = input("\nSuffix: ")
                    to_check = (to_check[0] + " " + addition, to_check[1])
                    useful.append(to_check)
                    last.append(1)
                    to_print = "<ForestGreen>Added as %s</ForestGreen>".ljust(100) % (to_check[0])
                    break


                elif decision == "f":
                    useless.append(to_check)
                    last.append(0)
                    to_print = "<crimson>" + to_check[0].ljust(max + 2) + \
                               "</crimson>f: <crimson>useless</crimson> - j: useful - b: back - x: interrupt"
                    break

                # revert a decision. Useful, since one can get quite inaccurate after a few hundred
                # words.
                elif decision == "b" and counter > 0:
                    last_useful = last[counter - 1]
                    if last_useful:
                        del useful[-1]
                    else:
                        del useless[-1]
                    del last[-1]
                    counter -= 2
                    break

                # break out of the outer loop and ending the selection process by
                # raising an exception.
                elif decision == "x":
                    raise BreakIt

            if is_new:
                print_formatted_text(HTML(to_print))
                counter += 1

    except BreakIt:
        pass

    print()
    save_lists(useless, useful, filepath)

    return useful, useless


# read out the occupation of a person with the previously created list.
def read_occupations(frame, useful):
    frame['occupation'] = "None"

    print("Reading out occupations")
    start = time()
    counter = 0
    for i, row in frame.iterrows():
        print(str(counter).ljust(5), "/", len(frame), end="\r")
        for occupation in useful:
            try:
                if occupation[0] in row['description'].lower():
                    row['occupation'] = occupation[0]
                    break
            except (TypeError, AttributeError):
                pass

        counter += 1

    print("\n", time() - start)

    success = frame[frame['occupation'] != "None"]
    fail = frame[frame['occupation'] == "None"]

    return success, fail


# assign a numerical value to each occupation and zodiac to make certain
# statistics possible.
def numerical_zodiac(zodiacs):
    zod_list = list(zodiacs.zodiac.unique())
    occ_list = list(zodiacs.occupation.unique())

    zod_numerical = pd.DataFrame()
    zod_numerical['zodiac'] = [0] * len(zodiacs)
    zod_numerical['occupation'] = [0] * len(zodiacs)

    counter = 0
    for i, row in zodiacs.iterrows():
        print(str(counter).ljust(5), "/", len(zodiacs), end='\r')
        zod_numerical.loc[i]['zodiac'] = zod_list.index(row['zodiac'])
        zod_numerical.loc[i]['occupation'] = occ_list.index(row['occupation'])
        counter += 1

    return zod_numerical


# run that shit
def run():
    frame = load_data()
    sorted_words = read_words(frame)
    useful, useless = check_words(sorted_words)

    # wildcard sports just in case.
    sports = [x + " player" for x in "football baseball basketball soccer".split(" ")]

    for i in sports:
        useful.append((i, 0))

    success, fail = read_occupations(frame, useful)

    zodiacs = pd.DataFrame()
    zodiacs['zodiac'] = success['zodiac']
    zodiacs['occupation'] = success['occupation']
    zodiacs = zodiacs.reset_index(drop=True)

    return zodiacs


if __name__ == "__main__":
    # execute only if run as a script
    getch = _Getch()
    sel = ""
    while sel not in ("y", "n"):
        print("Run program? [y]es, [n]o")
        sel = getch()

    # select "y" to get those sweet, sweet results.
    if sel == "y":
        zodiacs = run()
        zod_numerical = numerical_zodiac(zodiacs)
