from argparse import ArgumentParser
from lxml import html, etree
from lxml.builder import E
from pathlib import Path
from urllib.request import urlopen, urlretrieve
import re

def format_xpath_text(xpath):
    if not xpath:
        return ''
    return xpath[0].strip()


def get_title(root):
    return format_xpath_text(root.xpath(
        './/h2[@class="mb-3 w-full text-3xl font-bold text-primary"]/text()'))


def get_year(root):
    return format_xpath_text(root.xpath(
        './/span[@class="whitespace-normal p-1 text-secondary"]/text()'))\
            .replace('(','').replace(')','')


def get_studio(root):
    return format_xpath_text(root.xpath(
        './/a[@class="link link-secondary whitespace-normal capitalize"]/text()'))


def get_plot(root):
    return format_xpath_text(root.xpath(
        './/div[@class="w-full whitespace-pre-line break-words italic"]/text()'))


def get_skaters(root):
    return root.xpath(
        './/div[@class="self-start py-4 w-full"]/ul/li/a/span/text()')


def download_poster(root, videopath):
    img_url = root.find('.//meta[@property="og:image"]').attrib['content']
    if img_url != None:
        posterpath = videopath.parent/(videopath.stem+'-poster'+Path(img_url).suffix)
        print('  Downloading poster: ', posterpath)
        urlretrieve(img_url, posterpath)


def search(q):
    base_url = 'https://www.skatevideosite.com'
    search_url = base_url + '/search?q=' + q.replace(' ','+') + '&tab=1'
    root = html.parse(urlopen(search_url)).getroot()
    search_result = root.find('.//div[@data-tab-value="1"]//a[@href]')
    if search_result is None:
      return None
    return base_url + search_result.attrib['href']


def write_nfo(root, uid, nfopath):
    nfo = E.movie(
        E.title(get_title(root)),
        E.plot(get_plot(root)),
        E.studio(get_studio(root)),
        E.premiered(get_year(root)+'-01-01'),
        E.uniqueid(uid, {"type":"svs", "default":"true"}),
        E.genre("skate"),
        E.tag("skate"),
        *[E.actor(E.name(actor)) for actor in get_skaters(root)]
    )
    etree.ElementTree(nfo).write(
        nfopath,
        xml_declaration='True',
        encoding='UTF-8',
        standalone=True,
        pretty_print=True,
    )


def parse_cli():
    parser = ArgumentParser(
        prog = 'svscraper',
        description = 'Scrapes video inforomation from skatevideosite.com and '
            ' saves in Kodi\'s format.',
        epilog = 'source: https://github.com/xbeefier/svscraper')
    parser.add_argument(
        'videopath',
        type=Path,
        help='Path to a video file. The video file does not need to exist,'\
            ' svscraper will use the name of the file for searching the'\
            ' database and to name the generated .nfo and poster image.')
    parser.add_argument(
        '--ignore-brackets',
        action='store_true',
        help='Ignores bracket tags in videopath when searching the database.'\
            ' This does not affect the output data though, .nfo and poster'\
            ' will still use the same name as videopath')
    return parser.parse_args()


if __name__=="__main__":
    args = parse_cli()
    print('Input file: ', args.videopath)

    # option: --ignore-brackets
    if args.ignore_brackets:
        search_str = re.sub('\[.*?\]', '', args.videopath.stem)
    else:
        search_str = args.videopath.stem

    # search for video URL
    search_str = re.sub(r'[^\x00-\x7F]+','', search_str) # remove non-ascii
    print('  Searching for: ', search_str)
    url = search(search_str)
    if not url:
        print('  Could not find any video URL. Aborting.')
        quit()
    print('  Found ULR: ', url)

    # writing data
    root = html.parse(urlopen(url)).getroot()

    nfopath = args.videopath.with_suffix('.nfo')
    print('  Creating .nfo: ', nfopath)
    write_nfo(root, Path(url).name, nfopath)
    download_poster(root, args.videopath)
