#!/usr/bin/env python3

import urllib.request
import yaml
import datetime
import sys
from collections import OrderedDict
from bs4 import BeautifulSoup


_mapping_tag = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG

def dict_representer(dumper, data):
    return dumper.represent_dict(data.items())

def dict_constructor(loader, node):
    return OrderedDict(loader.construct_pairs(node))

yaml.SafeDumper.add_representer(OrderedDict, dict_representer)
yaml.SafeLoader.add_constructor(_mapping_tag, dict_constructor)


class Mensa:
    weekdays_short = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
    weekdays_long = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
    cafeteria_overview = "http://www.studentenwerk-berlin.de/mensen/speiseplan/index.html"
    cafeteria_detail = "http://www.studentenwerk-berlin.de/mensen/speiseplan/{cafeteria}/{day}.html"
    this_week = "http://www.studentenwerk-berlin.de/print/mensen/speiseplan/{cafeteria}/woche.html"
    next_week = "http://www.studentenwerk-berlin.de/print/mensen/speiseplan/{cafeteria}/naechste_woche.html"
    cafeterias = ["tu", "tu_cafe_erp", "tu_cafe_skyline", "tu_marchstr"]
    menu_file = "menus.yaml" # menu cache file
    prices = ["students", "staff", "guests"]
    price = "students"
    auto_dump = False

    def __init__(self, **kwargs):
        if "auto_dump" in kwargs:
            self.auto_dump = kwargs["auto_dump"]
        self.menu = OrderedDict()
        self.menu_dirty = False
        try:
            with open(self.menu_file) as f:
                self.menu = yaml.safe_load(f)
        except:
            pass

    def update_menu(self, cafeteria, *, auto_dump=None):
        """
        Update the menu for the next two weeks.
        """
        if auto_dump is None:
            auto_dump = self.auto_dump

        for week in [self.this_week, self.next_week]:
            with urllib.request.urlopen(week.format(cafeteria=cafeteria)) as f:
                html = BeautifulSoup(f.read().decode("utf8"), "html.parser")
                mensa_week_table = html.find(class_="mensa_week_table")
                mensa_week_table_rows = mensa_week_table.find_all("tr")
                mensa_week_head_cols = mensa_week_table_rows[0].find_all("th", class_="mensa_week_head_col")
                dates = []
                for col in mensa_week_head_cols:
                    weekday, date = col.text.split(", ")
                    date = datetime.date(*map(int, date.split(".")[::-1]))
                    assert date.weekday() == self.weekdays_short.index(weekday)
                    dates.append(date)

                for date in dates:
                    self.menu.setdefault(cafeteria, OrderedDict())[date] = OrderedDict()

                for row in mensa_week_table_rows[1:]:
                    category = row.find("th", class_="mensa_week_speise_tag_title").text
                    mensa_week_speise_tage = row.find_all("td", class_="mensa_week_speise_tag")
                    for weekday, mensa_week_speise_tag in enumerate(mensa_week_speise_tage):
                        dishes = []
                        mensa_speisen = mensa_week_speise_tag.find_all("p", class_="mensa_speise")
                        for mensa_speise in mensa_speisen:
                            name, subname = list(mensa_speise)[:2]
                            name = name.text.strip()
                            subname = str(subname).strip()
                            zusaetze = mensa_speise.find_all("a", class_="zusatz")
                            additives = [zusatz["title"] for zusatz in zusaetze]
                            mensa_preise = mensa_speise.find("span", class_="mensa_preise").text.strip("EUR ").split(" / ")
                            price = []
                            for mensa_preis in mensa_preise:
                                try:
                                    price.append(float(mensa_preis))
                                except ValueError:
                                    price.append(0)
                            dish = OrderedDict()
                            dish["name"] = name
                            if subname:
                                dish["subname"] = subname
                            dish["additives"] = additives
                            dish["price"] = price
                            dishes.append(dish)
                            self.menu[cafeteria][dates[weekday]][category] = dishes
                            self.menu_dirty = True

        # delete menus before today
        today = datetime.date.today()
        for date in list(self.menu[cafeteria].keys()):
            if date < today:
                del self.menu[cafeteria][date]
                self.menu_dirty = True

        if auto_dump:
            self.dump_menu()

    def dump_menu(self):
        """
        Write menu to file.
        """
        if not self.menu or not self.menu_dirty:
            return
        with open(self.menu_file, "w") as f:
            yaml.safe_dump(self.menu, f, allow_unicode=True)
        self.menu_dirty = False

    def filter(self, name=None, days=None, cafeterias=None, categories=None):
        """
        Filter the menu.
        """
        if name is None:
            name = [[]]
        if not days:
            today = datetime.date.today()
            if today.weekday() >= 5:
                today += datetime.timedelta(days=7-today.weekday())
            days = [today]
        if cafeterias is None:
            cafeterias = self.cafeterias
        if not categories:
            categories = []
        neg_categories = [c[1:] for c in categories if c[0] == "-"]
        categories = [c for c in categories if c[0] != "-"]

        # update menu
        missing = set()
        for cafeteria in cafeterias:
            if cafeteria not in self.menu:
                missing.add(cafeteria)
                continue
            cafeteria_menu = self.menu[cafeteria]
            for day in days:
                if day not in cafeteria_menu:
                    missing.add(cafeteria)
                    break
        for cafeteria in missing:
            self.update_menu(cafeteria, auto_dump=False)
        if missing:
            self.dump_menu()

        # filter
        for day in days:
            for cafeteria in cafeterias:
                for category, menu in self.menu[cafeteria][day].items():
                    if categories and category.lower() not in categories:
                        continue
                    if neg_categories and category.lower() in neg_categories:
                        continue
                    for food in menu:
                        for name1 in name:
                            success = True
                            for name2 in name1:
                                if name2 not in food["name"].lower() and name2 not in food.get("subname", "").lower():
                                    success = False
                            if success:
                                print(day, format(self.weekdays_long[day.weekday()], ""), cafeteria, "%s:" % category, food["name"] + (" - " + food["subname"] if "subname" in food else ""), food["price"][self.prices.index(self.price)])

    def parse_days(self, value):
        """
        Parse a list of weekdays to days.
        """
        if value.strip() == "all":
            value = ",".join(self.weekdays_short[:5])
        parts = value.strip(" ,").split(",")
        today = datetime.date.today()
        days = set()
        for day in parts:
            if day == "today":
                days.add(today)
            else:
                weekday = self.weekdays_short.index(day)
                days.add(today + datetime.timedelta(days=(weekday - today.weekday() - 1) % 7 + 1))
        return list(sorted(day for day in days if day.weekday() < 5))

    def parse_cafeterias(self, value):
        """
        Split cafeteria names.
        """
        cafeterias = value.strip(" ,").split(",")
        return cafeterias

    def parse_categories(self, value):
        """
        Split category names.
        """
        categories = value.strip(" ,").lower().split(",")
        return categories

    def parse_filters(self, value):
        """
        Parse filters as disjunctions of conjunctions.
        """
        def parse_and_filters(value):
            return value.strip(" &").split("&")
        parts = value.lower().strip(" |").split("|")
        filters = [parse_and_filters(p) for p in parts]
        return filters


def print_help():
    print("Usage example:", sys.argv[0], "'Salat&Champignon|Lachs' days=Mo,Di,Fr cafeterias=tu,tu_marchstr categories=Salate,Aktionsstand")


def main():
    m = Mensa(auto_dump=True)

    name = None
    days = None
    cafeterias = None
    categories = None

    argv = sys.argv[1:]
    if len(argv) >= 1 and "=" not in argv[0]:
        if argv[0] in ("-h", "--help"):
            print_help()
            sys.exit(1)
        name = m.parse_filters(argv.pop(0))
    for arg in argv:
        if "=" in arg:
            key, value = arg.split("=", 1)
            if key in ("day", "days"):
                try:
                    days = m.parse_days(value)
                except ValueError:
                    print("cannot parse argument value '%s'" % value)
            elif key in ("cafeteria", "cafeterias"):
                cafeterias = m.parse_cafeterias(value)
            elif key in ("category", "categories"):
                categories = m.parse_categories(value)
            else:
                print("cannot parse argument key '%s'" % key)
        else:
            print("cannot parse argument '%s'" % arg)

    m.filter(name=name, days=days, cafeterias=cafeterias, categories=categories)


if __name__ == "__main__":
    main()
