# Skate Videos Scraper

Scrapes information from [skatevideosite.com](https://www.skatevideosite.com)
and saves in [Kodi](https://kodi.tv)'s format.

## Dependencies
```
pip install argparse lxml pathlib re urllib
```

## Usage
```
$python svscraper.py --help
usage: svscraper [-h] [--ignore-brackets] videopath

Scrapes video inforomation from skatevideosite.com and saves in Kodi's
format.

positional arguments:
  videopath          Path to a video file. The video file does not
                     need to exist, svscraper will use the name of the
                     file for searching the database and to name the
                     generated .nfo and poster image.

options:
  -h, --help         show this help message and exit
  --ignore-brackets  Ignores bracket tags in videopath when searching
                     the database. This does not affect the output
                     data though, .nfo and poster will still use the
                     same name as videopath
```

Currently `svscraper.py` only scrapes one file at a time. A simple alternative
is to use script shell commands to call it multiple times.
Here is an example for Linux users using `find` to list all .webm movies in
a directory and pass it to `xargs` to run the svscraper for each file found:
```
find ./videos_dir -iname *.webm -printf '"%p"\n' | xargs -I{} python -u svscraper.py {}
```

# TODO
- Match year in the videopath with search results to minimize mistakes.
- Scrape skaters data.
- Add a cache system.
