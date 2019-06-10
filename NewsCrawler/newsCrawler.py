import pandas
import requests
from lxml import etree
from multiprocessing import Pool
import multiprocessing
import time
import re


def fetch(url):
    session = requests.Session()
    if 'appledaily.com' in url or url.startswith('/appledaily'):
        session.headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'}
    res = session.get(url)
    global startTime
    print('\r{:.1f}s '.format(time.time()-startTime), end='', flush=True)
    return res.text


def chinatimes(entry):
    title = entry.xpath('//*[@id="Head1"]/meta[@name="title"]')
    content = entry.xpath('//*[@id="Head1"]/meta[@name="description"]')[0].get('content')
    if content == '':
        content = entry.xpath('string(//div[contains(@class,"article-body")])')
    return title[0].get('content'), content


def udn(entry):
    title = entry.xpath('string(//*[@id="story_art_title"])')
    content = ''.join(entry.xpath('//*[@id="story_body_content"]/p/text()'))
    if content == '':
        content = ''.join(entry.xpath('//section[@id="story-main"]/p/a/strong/text()|//section[@id="story-main"]/p/text()'))
    return title, content


def ltn(entry):
    title = entry.xpath('//div[contains(@class, "whitecon articlebody")]/h1/text()')
    content = entry.xpath('//div[contains(@class, "text")]/p[not(contains(@class, "appE1121"))]/text()|//div[contains(@class, "text")]/h4/text()')
    return title[0], ''.join(content)


def tvbs(entry):
    title = entry.xpath('string(//h1[contains(@class,"margin_b20")])')
    content = entry.xpath('string(//div[@id="news_detail_div"])')
    if content == '':
        content = entry.xpath('string(//div[contains(@class,"h7 margin_b20")])')
    return title, content


def appledaily(entry):
    title = entry.xpath('string(//div[contains(@class, "nm-article")]/header/h2)')
    content = entry.xpath('string(//div[contains(@class,"nm-article-body")])')
    return title, content


def getContents(data):
    links = []
    for row in data.iloc[:, 1]:
        if row.startswith('/appledaily'):
            row = 'https://tw.appledaily.com' + row
        links.append(row)

    with Pool(processes=multiprocessing.cpu_count()) as pool:
        contents = pool.map(fetch, links)
        return contents


startTime = time.time()
for n in range(500):
    print('\nPart[{0}]'.format(n))
    data = pandas.read_csv('NC_1.csv', skiprows=n*200+1, nrows=200, header=None)
    contents = getContents(data)
    for index in range(data.shape[0]):
        url = data.iloc[index, 1]
        try:
            content = etree.HTML(contents[index])
            if 'udn.com' in url:
                title, content = udn(content)
            if 'ltn.com' in url:
                title, content = ltn(content)
            if 'chinatimes.com' in url:
                title, content = chinatimes(content)
            if 'tvbs.com' in url:
                title, content = tvbs(content)
            if 'appledaily.com' in url or url.startswith('/appledaily'):
                title, content = appledaily(content)
            data.loc[index, 'title'] = re.sub(r"[\n\t\s]*", "", title)
            data.loc[index, 'content'] = re.sub(r"[\n\t\s]*", "", content)
        except Exception as e:
            print(url + '/' + str(e))
    data.to_csv('out.csv', mode='a', header=0, index=0, sep=',', encoding='utf-8-sig')
