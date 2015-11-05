# Mensa

Tool for filtering the menus of the canteens and cafeterias of Studentenwerk Berlin on the command line.

## Usage

**Menu for all preferred cafeterias for today:**
```bash
$ python3 mensa.py
```

### Filter by days
**Menu for all preferred cafeterias for today and for the next Monday and Tuesday:**
```bash
$ python3 mensa.py days=today,Mo,Di
```

**Menu for all preferred cafeterias for the following 5 days:**
```bash
$ python3 mensa.py days=all
```

### Filter by cafeterias
**Menu for cafeteria Marchstraße and TU Hauptmensa:**
```bash
$ python3 mensa.py cafeterias=tu_marchstr,tu
```

Some other cafeterias:

* tu_cafe_skyline (TEL)
* tu_cafe_erp (A)

### Filter by categories
**Only salads and desserts:**
```bash
$ python3 mensa.py categories=Salate,Desserts
```

**No soups:**
```bash
$ python3 mensa.py categories=-Suppen
```

Frequent categories:

* Vorspeisen
* Salate
* Suppen
* Aktionsstand
* Essen
* Beilagen
* Desserts

### Filter by name
Has to be the first argument.

**With French fries or with tomatoes and cheese:**
```bash
$ python3 mensa.py 'Pommes|Tomate&Käse'
```
(case-insensitive)

**All filters combined:**
```bash
$ python3 mensa.py 'Salat&Champignon|Lachs' days=Mo,Di,Fr cafeterias=tu,tu_marchstr categories=Salate,Aktionsstand
```
