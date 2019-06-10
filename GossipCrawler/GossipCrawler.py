import requests
import csv
import re
from lxml import etree
from pyquery import PyQuery
from requests_html import HTML

domain = 'https://www.ptt.cc/'


def fetch_web(url):
    response = requests.get(url, cookies={'over18': '1'})
    return response


def prase_current_page(url):

    def last_page_link(doc):
        controls = HTML(html=doc).find('.action-bar a.btn.wide')
        link = controls[1].attrs['href']
        return domain+link

    res = fetch_web(url)
    post_entries = HTML(html=res.text).find('div.r-ent')
    post_entries.reverse()
    prev_link = last_page_link(res.text)
    return post_entries, prev_link


def get_post_entries(url, pages):
    poes = []
    for _ in range(pages):
        posts, plink = prase_current_page(url)
        poes += posts
        url = plink
    return poes


def prase_article_entry(url):
    res = fetch_web(url)
    article_entry = HTML(html=res.text)
    return article_entry


def parse_content(article_entry):
        content_ent = article_entry.find('#main-content')[0]
        exclude_classes = [
            '.article-metaline', '.article-metaline-right', '.push']
        exclude_text_spans = ['發信站: 批踢踢實業坊(ptt.cc)', '文章網址:']

        for exclude_text in exclude_text_spans:
            ele = content_ent.lxml.xpath(
                f'//span[contains(text(),"{exclude_text}")]')[0]
            ele.getparent().remove(ele)
        cleaned_html = etree.tostring(content_ent.lxml)

        cleaned_pq = PyQuery(cleaned_html)
        for exclude_cls in exclude_classes:
            cleaned_pq.remove(exclude_cls)

        return cleaned_pq.text()


def parse_comment(article_entry, post_id):
    def get_comment():
        for push in article_entry.find('div.push'):
            yield push.find('span')

    tag_count = {'推': 0, '噓': 0, '→': 0}
    with open(str(post_id) + '.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['tag', 'author', 'comment', 'date'])
        for p in get_comment():
            if p:
                tag_count[p[0].text.strip()] += 1
                writer.writerow(
                    [p[0].text.strip(), p[1].text.strip(),
                     p[2].text[1:].strip(), p[3].text.strip()])
    return tag_count


url = 'https://www.ptt.cc/bbs/Gossiping/index.html'
poes = get_post_entries(url, 10)
post_id = 0
with open('gossip.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(
        ['id', 'title', 'date', 'author', 'content-url',
         'ipaddress', 'content', 'push', 'down', 'arrow'])

    for entry in poes:
        title = entry.find('div.title', first=True).text
        if title.startswith(('本文已被刪除', '[公告]')) or re.search('已被\w*刪除', title):
            continue
        date = entry.find('div.date', first=True).text
        author = entry.find('div.author', first=True).text
        link = domain + entry.find('div.title > a', first=True).attrs['href']
        article_ent = prase_article_entry(link)
        ip = article_ent.xpath(
            '//*[@id="main-content"]'
            '/span[contains(text(),"發信站: 批踢踢實業坊(ptt.cc)")]')[0].text[27:]
        content = parse_content(article_ent)
        push = parse_comment(article_ent, post_id)
        print(post_id, title, date, author)
        writer.writerow(
            [post_id, title, date, author, link, ip,
             content, push['推'], push['噓'], push['→']])
        post_id += 1

"""
    content = article_ent.xpath(
            '//div[@id="main-content"]'
            '/text()['
            'not(contains(@class, "push")) and '
            'not(contains(@class, "article-metaline")) ]'
            '|//div[@id="main-content"]/a/@href'
            '|//div[@id="main-content"]/span[starts-with(text(),"※ 引述") or'
            'starts-with(text(),":") ]/text()')
"""

