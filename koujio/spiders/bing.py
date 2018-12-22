#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018-12-22 12:20
# @Author  : pang
# @File    : bing.py
# @Software: PyCharm
import asyncio
import logging
from urllib.parse import urlparse

import aiohttp
import async_timeout
from bs4 import BeautifulSoup
from owllook.config.rules import *


def get_random_user_agent():
    return "Mozilla/4.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/5.0)"


async def data_extraction(html):
    """
    小说信息抓取函数
    :return:
    """
    try:
        title = html.select('h2 a')[0].get_text()
        url = html.select('h2 a')[0].get('href', None)
        netloc = urlparse(url).netloc
        url = url.replace('index.html', '').replace('Index.html', '')
        if not url or 'baidu' in url or 'baike.so.com' in url or netloc in BLACK_DOMAIN or '.html' in url:
            return None
        is_parse = 1 if netloc in RULES.keys() else 0
        is_recommend = 1 if netloc in LATEST_RULES.keys() else 0
        timestamp = 0
        time = ''
        return {'title': title,
                'url': url,
                'time': time,
                'is_parse': is_parse,
                'is_recommend': is_recommend,
                'timestamp': timestamp,
                'netloc': netloc}

    except Exception as e:
        logging.exception(e)
        return None

async def fetch_url(url, params, headers):
    """
    公共抓取函数
    :param url:
    :param params:
    :return:
    """
    with async_timeout.timeout(15):
        try:
            async with aiohttp.ClientSession() as client:
                async with client.get(url, params=params, headers=headers) as response:
                    assert response.status == 200
                    logging.info('Task url: {}'.format(response.url))
                    try:
                        text = await response.text()
                    except:
                        text = await response.read()
                    return text
        except Exception as e:
            logging.exception(e)
            return None


async def novels_search(novels_name):
    """
    小说搜索入口函数
    :return:
    """
    url = "https://www.bing.com/search"
    headers = {
        'user-agent': get_random_user_agent(),
        'referer': "https://www.bing.com/"
    }
    params = {'q': novels_name, 'ensearch': 0}
    html = await fetch_url(url=url, params=params, headers=headers)
    if html:
        soup = BeautifulSoup(html, 'html5lib')
        result = soup.find_all(class_='b_algo')
        extra_tasks = [data_extraction(html=i) for i in result]
        tasks = [asyncio.ensure_future(i) for i in extra_tasks]
        done_list, pending_list = await asyncio.wait(tasks)
        res = [task.result() for task in done_list if task.result()]
        return res
    else:
        return []


if __name__ == '__main__':
    res = asyncio.get_event_loop().run_until_complete(novels_search('雪中悍刀行 小说 阅读 最新章节'))
    print(res)

