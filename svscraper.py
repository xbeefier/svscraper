from argparse import ArgumentParser
from difflib import SequenceMatcher
from pathlib import Path
from urllib.request import urlopen, urlretrieve
from urllib.parse import quote
from xml.etree import ElementTree as ET
from xml.dom import minidom
from lxml import html  #TODO: lxml is not part of the standard library
import re

class VideoPath:
    def __init__(self, path):
        self.company = None
        self.year = None
        self.video_name = None
        self.sourceid = None
        self.path = path
        self._parse_video_name()
        self._parse_sourceid()

    def make_nfo(self):
        movie = ET.Element('movie')
        ET.SubElement(movie, 'title').text = self.video_name
        ET.SubElement(movie, 'studio').text = self.company
        ET.SubElement(movie, 'premiered').text = self.year+'-01-01'
        ET.SubElement(movie, 'uniqueid', {'type':'home', 'default':'true'}
            ).text = self.video_name.lower().replace(' ','-')
        ET.SubElement(movie, 'genre').text = 'skate'
        ET.SubElement(movie, 'tag').text = 'skate'
        return ET.tostring(movie)
        

    def _parse_company(self):
        match = re.match(r'^[^-]*', self.path.stem)
        if match:
            self.company = match.group(0).strip()

    def _parse_year(self):
        match = re.search(r'(?<=\()\d{4}(?=\))', self.path.stem)
        if match:
            self.year = match.group(0).strip()

    def _parse_video_name(self):
        self._parse_company()
        self._parse_year();
        self.video_name = self.path.stem
        if self.company:
            self.video_name = re.sub(r'^[^-]*-','', self.video_name)
        if self.year:
            self.video_name = re.sub(r'\(\d{4}\)', '', self.video_name)
        self.video_name = re.sub(r'\[[^]]+\]', '', self.video_name) #strip tags
        self.video_name = self.video_name.strip()

    def _parse_sourceid(self):
        match = re.search(r'(?<=\[svs=)[^]]+', self.path.stem)
        if match:
            self.sourceid = match.group(0).strip()


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
    if img_url and re.match('^https://assets.skatevideo.site/covers/', img_url):
        posterpath = videopath.parent/(videopath.stem+'-poster'+Path(img_url).suffix)
        print('  Downloading poster: ', posterpath)
        urlretrieve(img_url, posterpath)


def search(vp):
    base_url = 'https://www.skatevideosite.com'
    search_str = quote(vp.video_name.replace(' ','+'))
    search_url = base_url+'/search?q='+search_str+'&tab=1'
    root = html.parse(urlopen(search_url)).getroot()
    tab1 = root.find('.//div[@data-tabs-target="contents"]/div[@data-tab-value="1"]')
    weights = []
    for i,div in enumerate(tab1):
        year = format_xpath_text(div.xpath(
            './/span[@class="ml-2 text-base font-semibold"]/text()'))
        if year != '(0)':
            year = re.search('\d{4}',year).group(0)
        company = format_xpath_text(div.xpath(
            './/a[@class="link link-secondary capitalize"]/text()')).strip()
        href = div.find(
            './/a[@class="font-semibold text-primary underline"][@href]'
            ).attrib['href']
        weights.append([0,href])
        weights[-1][0] += 1/(i+1)
        weights[-1][0] += 1 if year == vp.year else 0
        weights[-1][0] += SequenceMatcher(None, company, vp.company).ratio()
    if not weights:
        return None
    weights = sorted(weights, key=lambda w: w[0])
    return base_url + weights[-1][1]


def make_nfo(root, uid):
    movie = ET.Element('movie')
    ET.SubElement(movie, 'title').text = get_title(root)
    ET.SubElement(movie, 'plot').text = get_plot(root)
    ET.SubElement(movie, 'studio').text = get_studio(root)
    ET.SubElement(movie, 'premiered').text = get_year(root)+'-01-01'
    ET.SubElement(movie, 'uniqueid', {'type':'home', 'default':'true'}
        ).text = uid
    ET.SubElement(movie, 'genre').text = 'skate'
    ET.SubElement(movie, 'tag').text = 'skate'
    for skater in get_skaters(root):
        actor = ET.SubElement(movie, 'actor')
        ET.SubElement(actor, 'name').text = skater
    return ET.tostring(movie)


def write_nfo(nfopath, nfo):
    minidom.parseString(nfo).writexml(open(nfopath,'w'), indent='',
        addindent='  ', newl='\n', encoding='utf-8', standalone=True)


def parse_cli():
    parser = ArgumentParser(prog = 'svscraper',
        description = 'Scrapes video inforomation from skatevideosite.com and '
            ' saves in Kodi\'s format.',
        epilog = 'source: https://github.com/xbeefier/svscraper')
    parser.add_argument('videopath', type=Path,
        help='Path to a video file. The video file does not need to exist,'\
            ' svscraper will use the file name for searching the database'\
            ' and to name the generated .nfo and poster image.'\
            ' Prefered naming convention is "Company - VideoName (YEAR).mp4",'\
            ' this way search results are more accurate and in case data is not'\
            ' found a minimal .nfo will still be generated using the data in'\
            ' the file name.')
    return parser.parse_args()


if __name__=="__main__":
    args = parse_cli()
    vp = VideoPath(args.videopath)
    print('Searching data for video file: ', vp.path)
    url = search(vp)
    if url:
        print('  Scraping from:', url)
        root = html.parse(urlopen(url)).getroot()
        nfo = make_nfo(root, uid=Path(url).name)
        download_poster(root, vp.path)
    else:
        print('  Could not find any match. Using file name to create the .nfo file')
        nfo = vp.make_nfo()
    nfopath = vp.path.with_suffix('.nfo')
    print('  Creating .nfo: ', nfopath)
    write_nfo(nfopath, nfo)
