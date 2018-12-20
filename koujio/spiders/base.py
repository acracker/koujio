#!/usr/bin/env python
# -*- coding: utf-8 -*-

import aiohttp


class BaseFetcher(object):

    session = None

    def __init__(self, **kwargs):
        self.session = aiohttp.ClientSession(**kwargs)

    async def fetch(self, url, **kwargs):
        async with self.session.get(url=url, **kwargs) as response:
            return await response.text()

    async def close(self):
        await self.session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
