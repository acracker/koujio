#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import logging
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from operator import itemgetter
from collections import OrderedDict



def extract_chapters(chapters_url, html):
    """
    通用解析小说目录
    :param chapters_url: 小说目录页url
    :param html: 当前页面html
    :return:
    """
    # 参考https://greasyfork.org/zh-CN/scripts/292-my-novel-reader
    chapters_reg = r'(<a\s+.*?>.*第?\s*[一二两三四五六七八九十○零百千万亿0-9１２３４５６７８９０]{1,6}\s*[章回卷节折篇幕集].*?</a>)'
    # 这里不能保证获取的章节分得很清楚，但能保证这一串str是章节目录。可以利用bs安心提取a
    chapters_res = re.findall(chapters_reg, str(html), re.I)
    str_chapters_res = '\n'.join(chapters_res)
    chapters_res_soup = BeautifulSoup(str_chapters_res, 'html5lib')
    all_chapters = {}
    for link in chapters_res_soup.find_all('a'):
        each_data = {}
        url = urljoin(chapters_url, link.get('href')) or ''
        name = link.text or ''
        each_data['chapter_url'] = url
        each_data['chapter_name'] = name
        each_data['index'] = int(urlparse(url).path.split('.')[0].split('/')[-1])
        all_chapters[each_data['index']] = each_data
    chapters_sorted = sorted(all_chapters.values(), reverse=True, key=itemgetter('index'))
    return chapters_sorted


def extract_content(html, chapter_url=None):
    """
    从小说章节页面提取 小说内容以及 上下一章的地址
    :param html:小说章节页面内容
    :param chapter_url: 小说章节页面地址
    :return:
    """
    soup = BeautifulSoup(html, 'html5lib')
    selector = {'id': 'content'}
    if selector.get('id', None):
        content = soup.find_all(id=selector['id'])
    elif selector.get('class', None):
        content = soup.find_all(class_=selector['class'])
    else:
        content = soup.find_all(selector.get('tag'))
    if content:
        # 提取出真正的章节标题
        title_reg = r'(第?\s*[一二两三四五六七八九十○零百千万亿0-9１２３４５６７８９０]{1,6}\s*[章回卷节折篇幕集]\s*.*?)[_,-]'
        title = soup.title.string
        extract_title = re.findall(title_reg, title, re.I)
        if extract_title:
            title = extract_title[0]
        else:
            title = soup.select('h1')[0].get_text()
        if not title:
            title = soup.title.string
        # if "_" in title:
        #     title = title.split('_')[0]
        # elif "-" in title:
        #     title = title.split('-')[0]
        if chapter_url:
            next_chapter = extract_pre_next_chapter(chapter_url=chapter_url, html=str(soup))
        else:
            next_chapter = OrderedDict()
        content = [str(i) for i in content]
        data = {
            'content': str(''.join(content)),
            'next_chapter': next_chapter,
            'title': title
        }
    else:
        data = None
    return data


def extract_pre_next_chapter(chapter_url, html):
    """
    获取单章节上一页下一页
    :param chapter_url:
    :param html:
    :return:
    """
    next_chapter = OrderedDict()
    try:
        # 参考https://greasyfork.org/zh-CN/scripts/292-my-novel-reader
        next_reg = r'(<a\s+.*?>.*[第上前下后][一]?[0-9]{0,6}?[页张个篇章节步].*?</a>)'
        judge_reg = r'[第上前下后][一]?[0-9]{0,6}?[页张个篇章节步]'
        # 这里同样需要利用bs再次解析
        next_res = re.findall(next_reg, html.replace('<<', '').replace('>>', ''), re.I)
        str_next_res = '\n'.join(next_res)
        next_res_soup = BeautifulSoup(str_next_res, 'html5lib')
        for link in next_res_soup.find_all('a'):
            text = link.text or ''
            text = text.replace(' ', '')
            if novels_list(text):
                is_next = re.search(judge_reg, text)
                # is_ok = is_chapter(text)
                if is_next:
                    url = urljoin(chapter_url, link.get('href')) or ''
                    next_chapter[text[:5]] = url

        # nextDic = [{v[0]: v[1]} for v in sorted(next_chapter.items(), key=lambda d: d[1])]
        return next_chapter
    except Exception as e:
        logging.exception(e)
        return next_chapter


def novels_list(text):
    rm_list = ['后一个', '天上掉下个']
    for i in rm_list:
        if i in text:
            return False
        else:
            continue
    return True


async def target_fetch(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()


async def main():
    url = "https://www.xbiquge6.com/81_81273/"
    html = await target_fetch(url)
    chapters = extract_chapters(url, html)
    for chapter in chapters[-3:]:
        chapter_url = chapter['chapter_url']
        chapter_name = chapter['chapter_name']
        html = await target_fetch(chapter_url)
        data = extract_content(html, chapter_url)
        print(data['content'])



loop = asyncio.get_event_loop()
loop.run_until_complete(main())