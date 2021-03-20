#!/bin/python3

import bs4
import re
import wikipedia
import pandas as pd
import warnings
from time import time
from requests import get
from prompt_toolkit import print_formatted_text as print
from prompt_toolkit import HTML

# Download and store every person in the wikipedia birth register in a certain time interval.
# It is important that the following directory structure is given at the directory where the
# script will be run:

#   .
#   ├── zodiac.py
#   ├── analyse_occupations.py
#   └── zodiac_files
#       ├── bak/
#       ├── data/
#       ├── descriptions/
#       ├── failed/
#       ├── lists/
#       ├── no_birthday/
#       └── time/



#boring assignment of zodiac
def get_zodiac(day, month):

    if month == 'January':
        zodiac = 'Capricorn' if (day < 20) else 'Aquarius'
        zodiac_german = 'Steinbock' if (day < 20) else 'Wassermann'
    elif month == 'February':
        zodiac = 'Aquarius' if (day < 19) else 'Pisces'
        zodiac_german = 'Wassermann' if (day < 19) else 'Fische'
    elif month == 'March':
        zodiac = 'Pisces' if (day < 21) else 'Aries'
        zodiac_german = 'Fische' if (day < 21) else 'Widder'
    elif month == 'April':
        zodiac = 'Aries' if (day < 20) else 'Taurus'
        zodiac_german = 'Widder' if (day < 20) else 'Stier'
    elif month == 'May':
        zodiac = 'Taurus' if (day < 21) else 'Gemini'
        zodiac_german = 'Stier' if (day < 21) else 'Zwillinge'
    elif month == 'June':
        zodiac = 'Gemini' if (day < 21) else 'Cancer'
        zodiac_german = 'Zwillinge' if (day < 21) else 'Krebs'
    elif month == 'July':
        zodiac = 'Cancer' if (day < 23) else 'Leo'
        zodiac_german = 'Krebs' if (day < 23) else 'Löwe'
    elif month == 'August':
        zodiac = 'Leo' if (day < 23) else 'Virgo'
        zodiac_german = 'Löwe' if (day < 23) else 'Jungfrau'
    elif month == 'September':
        zodiac = 'Virgo' if (day < 23) else 'Libra'
        zodiac_german = 'Jungfrau' if (day < 23) else 'Waage'
    elif month == 'October':
        zodiac = 'Libra' if (day < 23) else 'Scorpio'
        zodiac_german = 'Waage' if (day < 23) else 'Skorpion'
    elif month == 'November':
        zodiac = 'Scorpio' if (day < 22) else 'Sagittarius'
        zodiac_german = 'Skorpion' if (day < 22) else 'Schütze'
    elif month == 'December':
        zodiac = 'Sagittarius' if (day < 22) else 'Capricorn'
        zodiac_german = 'Schütze' if (day < 22) else 'Steinbock'

    return zodiac, zodiac_german


def run(year=1900):

    # some variables for statistics
    start = time()
    people_counter = 0
    people_failed = 0
    people_no_birthday = 0
    page_counter = 0
    time_years = []
    time_pages = []

    # ignore bs4's warning that it guesses the parses. Does not happen often but is annoying
    # and also useless in this case, so turning it off
    warnings.filterwarnings("ignore", category=bs4.GuessedAtParserWarning)

    # needed for some operations on statistics and saving files, but most important
    # for ensuring the link is set to the first page of a new year.
    new_year = True

    # from here on it is just one big loop. The start year is given by the function parameter "year".
    # ending in 1969 because
    # 1. There is more than enough data at this point
    # 2. 69 :>

    while year < 1970:

        # initializing all the lists for storing the data
        names = []
        summaries = []
        descriptions = []
        birthdays = []
        zodiacs = []
        zodiacs_german = []
        failed = []
        no_birthday = []
        time_people = []

        # setting link for first page of a year and resetting yearly counter and timer
        if new_year:
            link = "https://en.wikipedia.org/wiki/Category:" + str(year) + "_births"
            time_year = time()
            people_counter_year = 0


        # creating soup for the index page and extract every person stored on it.
        page = get(link)
        soup = bs4.BeautifulSoup(page.text, "lxml")
        people_groups = soup.select(".mw-category-group")
        people = []

        # people are stored in a list of strings with one string for every person of a
        # given first character, each divided by a newline.
        # Here these strings are split up into lists of strings instead so they can be
        # unpacked
        for i in people_groups:
            people.append(i.text.split("\n"))

        # unpacking with a nested list comprehension. Also making sure the headers for
        # each subsection are not transfered to the new list of people, because they are
        # in the css-element as well.
        people = [person for sublist in people for person in sublist if len(person) > 1 and person != "0–9"]

        # counting pages of the current year. This does take some 30-60 seconds and is not really
        # necessary, but being able to see the progress during execution makes it worth it.
        # Besides the time "wasted" here does not really mater considering the complete runtime being
        # several days.
        if new_year:
            pages = 0
            pages_soup = soup
            while True:
                try:
                    href = pages_soup.findAll("a", href=True, text="next page")[0]["href"]
                    pages += 1
                    next_page = "https://en.wikipedia.org" + href
                    pages_soup = bs4.BeautifulSoup(get(next_page).text, "lxml")
                except IndexError:
                    break
            new_year = False

        to_print = "<crimson>---- Year: %d Page: %d/%d ----</crimson>" % (year, page_counter, pages)
        print(HTML(to_print))

        # regexes for filtering out the birthdate.
        birthday_regex = "\d{1,2}\s\w+\s" + str(year) + "|\w+\s\d{1,2},\s" + str(year)
        day_regex = "(^|\\s)\\d{1,2}\\D"
        month_regex = "[A-Z][a-z]+"

        # used later to assign a numerical month to the written ones of the wikipedia text.
        months = ["January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December"]

        # all the counters
        counter = 0
        counter_people = len(people)


        time_page = time()

        # looping through every person of the current page
        for person in people:

            # ALL the counters. Also timekeeping
            time_person = time()
            if counter % 50 == 0:
                print("Person %d/%d" % (counter, counter_people))
            counter += 1
            people_counter += 1
            people_counter_year += 1

            # Extracting the first sentence of the summary of the wikipedia via the wikipedia-API module
            # Blank excepts are not recommended, but the only thing that could happen here is that
            # the name that gets used is ambiguous, so.. ¯\_(ツ)_/¯
            try:
                summary = wikipedia.summary(person, sentences=1)
            except:
                failed.append(person)
                people_failed += 1
                continue

            # check for a valid birthday.
            # If there is none, scrap that person and begin next loop iteration.
            try:
                birthday = re.search(birthday_regex, summary).group(0)
                day = "".join([x for x in re.search(day_regex, birthday).group(0) if x.isdigit()])
                month = re.search(month_regex, birthday).group(0)
                month_num = str(months.index(month) + 1)
            except (AttributeError, ValueError):
                no_birthday.append(person)
                people_no_birthday += 1
                continue

            # If the current person got until here, it is mostly valid.
            # -> store the data in the lists and continue
            names.append(person)
            descriptions.append("".join(summary.split(")")[1:]))
            summaries.append(summary)

            birthdays.append(day + "." + month_num + "." + str(year))
            zodiac, zodiac_german = get_zodiac(int(day), month)
            zodiacs.append(zodiac)
            zodiacs_german.append(zodiac_german)
            time_people.append(time()-time_person)

        time_pages.append([year, page_counter, time()-time_page])

        # store lists of current page in dictionaries
        data = {'name': names, 'bday': birthdays, 'zodiac': zodiacs, 'zodiac_german': zodiacs_german,
                'description': descriptions, 'summary': summaries}
        description_data = {'description': descriptions, 'summary': summaries}
        time_data = {'name': names, 'time': time_people}

        # create pandas DataFrames of the dictionaries
        frame_data = pd.DataFrame(data)
        frame_description = pd.DataFrame(description_data)
        frame_failed = pd.DataFrame(failed)
        frame_no_birthday = pd.DataFrame(no_birthday)
        frame_time_people = pd.DataFrame(time_data)

        # set filepaths for .csv files
        filepath_data = "./zodiac_files/data/%d_%d.csv" % (year, page_counter)
        filepath_desc = "./zodiac_files/descriptions/%d_%d.csv" % (year, page_counter)
        filepath_failed = "./zodiac_files/failed/%d_%d.csv" % (year, page_counter)
        filepath_no_birthday = "./zodiac_files/no_birthday/%d_%d.csv" % (year, page_counter)
        filepath_time_people = "./zodiac_files/time/%d_%d_people.csv" % (year, page_counter)

        # save .csv files of the current page
        frame_data.to_csv(filepath_data, sep="$", index=False)
        frame_description.to_csv(filepath_desc, sep="$", index=False)
        frame_failed.to_csv(filepath_failed, sep="$", index=False)
        frame_no_birthday.to_csv(filepath_no_birthday, sep="$", index=False)
        frame_time_people.to_csv(filepath_time_people, sep="$", index=False)

        # check if there is another "next page"-button on the current page, and
        # assign the new link
        try:
            href = soup.findAll("a", href=True, text="next page")[0]["href"]
            page_counter += 1
            link = "https://en.wikipedia.org" + href

        # if there is no "next page"-button, save statistics of the current year
        # and initiate the new year
        except IndexError:
            year += 1
            page_counter = 0
            new_year = True
            time_years.append([year, time() - time_year])

            frame_year = pd.DataFrame(time_years, columns=["Year", "Time"])
            frame_pages = pd.DataFrame(time_pages, columns=["Year", "Page", "Time"])

            filepath_time_years = "./zodiac_files/time/years.csv"
            filepath_time_pages = "./zodiac_files/time/pages.csv"

            frame_year.to_csv(filepath_time_years, index=False)
            frame_pages.to_csv(filepath_time_pages, index=False)

            to_print = "<ForestGreen> --- People this year: <Gold>%d</Gold> -- People until now: <Gold>%d</Gold> ---</ForestGreen>" % (people_counter_year, people_counter)
            print(HTML(to_print))

    end = time()
    to_print = "<crimson>----! It is done - Total time: %d s - Total people: %d " \
               "(failed: %d, without birthday: %d) !----</crimson>" \
               % (end-start, people_counter, people_failed, people_no_birthday)
    print(HTML(to_print))

run()
