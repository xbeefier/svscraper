# Skate Videos Scraper

Scrapes information from [skatevideosite.com](https://www.skatevideosite.com)
and saves in [Kodi](https://kodi.tv)'s `.nfo` format.

## Dependencies
```
pip install lxml
```

## Usage
```
usage: svscraper [-h] videopath

Scrapes video inforomation from skatevideosite.com and saves in
Kodi's format.

positional arguments:
  videopath   Path to a video file. The video file does not need to
              exist, svscraper will use the file name for searching
              the database and to name the generated .nfo and poster
              image. Prefered naming convention is "Company -
              VideoName (YEAR).mp4", this way search results are more
              accurate and in case data is not found a minimal .nfo
              will still be generated using the data in the file
              name.

options:
  -h, --help  show this help message and exit
```

Currently `svscraper.py` only scrapes one file at a time. A simple alternative
is to use script shell commands to call it multiple times.
Here is an example for Linux users using `find` to list all .webm movies in
a directory and pass it to `xargs` to run the svscraper for each file found:
```
find ./videos_dir -iname *.webm -printf '"%p"\n' | xargs -I{} python -u svscraper.py {}
```

# TODO
- Scrape skaters data.
- Kodi add-on
- Add a cache system.
