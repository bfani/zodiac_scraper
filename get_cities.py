from requests import get
import bs4

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

def check_words(sorted_words):

    getch = _Getch()
    max = 0
    for word, occurences in sorted_words[0:200]:
        if len(word) > max:
            max = len(word)

    counter = 0
    last = []

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

                elif decision == "f":
                    useless.append(to_check)
                    last.append(0)
                    to_print = "<crimson>" + to_check[0].ljust(max + 2) + \
                               "</crimson>f: <crimson>useless</crimson> - j: useful - b: back - x: interrupt"
                    break

                elif decision == "b" and counter > 0:
                    last_useful = last[counter - 1]
                    if last_useful:
                        del useful[-1]
                    else:
                        del useless[-1]
                    del last[-1]
                    counter -= 2
                    break

                elif decision == "x":
                    raise BreakIt

            if is_new:
                print_formatted_text(HTML(to_print))
                counter += 1
    except BreakIt:
        pass

    print()
    save_files(useless, useful, filepath)
root = bs4.BeautifulSoup(get("https://en.wikipedia.org/wiki/Lists_of_cities").text, "lxml")

regions = root.select(".navbox")[0].find_all("a")

excluded = "Africa, The Americas, North America, South America, Asia, Europe, Oceania".split(", ")
cities = {}

counter = 0
for i in regions:
    if counter < 3:
        counter += 1
        continue

    if i.text not in excluded:

        page = bs4.BeautifulSoup(get("https://en.wikipedia.org" + i['href']).text, "lxml")
        links = page.find_all("a")

        try:
            for link in links:
                if not any(char.isdigit() for char in link.text):
                    link = link.text.lower()
                    if link in cities:
                        cities[link] += 1
                    else:
                        cities[link] = 1
        except IndexError:
            pass

sorted_cities = sorted(cities.items(), key=lambda kv: kv[1])[::-1]
