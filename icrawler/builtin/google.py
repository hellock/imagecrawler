# -*- coding: utf-8 -*-

import json

from bs4 import BeautifulSoup
from six.moves.urllib.parse import urlencode

from icrawler import Crawler, Feeder, Parser, ImageDownloader


class GoogleFeeder(Feeder):

    def feed(self,
             keyword,
             offset,
             max_num,
             date_min=None,
             date_max=None,
             language=None,
             img_type=None,
             img_color=None,
             usage_rights=None):
        base_url = 'https://www.google.com/search?'
        if usage_rights and usage_rights not in ['f', 'fc', 'fm', 'fmc']:
            # f: non-commercial reuse
            # fm: non-commercial reuse with modification
            # fc: reuse
            # fmc: reuse with modification
            raise ValueError(
                '"usage_rights" must be one of the following: f, fc, fm, fmc')
        if img_type and img_type not in [
                'photo', 'face', 'clipart', 'lineart', 'animated']:
            # photo
            # face
            # clipart: clip art
            # lineart: line drawing
            # animated
            raise ValueError(
                '"img_type" must be one of the following: '
                'photo, face, clipart, lineart, animated')
        if img_color and img_color not in [
                'color', 'blackwhite', 'transparent', 'red', 'orange', 'yellow',
                'green', 'teal', 'blue', 'purple', 'pink', 'white', 'gray',
                'black', 'brown']:
            # color: full color
            # blackwhite: black and white
            # transparent: transparent
            # red, orange, yellow, green, teal, blue, purple, pink, white, gray, black, brown
            raise ValueError(
                '"img_color" must be one of the following: '
                'color, blackwhite, transparent, red, orange, yellow, green, teal, '
                'blue, purple, pink, white, gray, black, brown')
        for i in range(offset, offset + max_num, 100):
            cd_min = date_min.strftime('%m/%d/%Y') if date_min else ''
            cd_max = date_max.strftime('%m/%d/%Y') if date_max else ''
            lang = 'lang_' + language if language else ''
            usage_rights = '' if usage_rights is None else usage_rights
            img_type = '' if img_type is None else img_type
            img_color = '' if img_color is None else img_color
            img_specific = ''
            if img_color not in ['', 'color', 'blackwhite', 'transparent']:
                img_specific = img_color
                img_color = 'specific'
            elif img_color == 'blackwhite':
                img_color = 'gray'
            elif img_color == 'transparent':
                img_color = 'trans'
            tbs = 'cdr:1,cd_min:{},cd_max:{},sur:{},itp:{},ic:{},isc:{}'.format(
                cd_min, cd_max, usage_rights, img_type, img_color, img_specific)
            params = dict(
                q=keyword,
                ijn=int(i / 100),
                start=i,
                tbs=tbs,
                tbm='isch',
                lr=lang)
            url = base_url + urlencode(params)
            self.out_queue.put(url)
            self.logger.debug('put url to url_queue: {}'.format(url))


class GoogleParser(Parser):

    def parse(self, response):
        soup = BeautifulSoup(
            response.content.decode('utf-8', 'ignore'), 'lxml')
        image_divs = soup.find_all('div', class_='rg_meta')
        for div in image_divs:
            meta = json.loads(div.text)
            if 'ou' in meta:
                yield dict(file_url=meta['ou'])


class GoogleImageCrawler(Crawler):

    def __init__(self,
                 feeder_cls=GoogleFeeder,
                 parser_cls=GoogleParser,
                 downloader_cls=ImageDownloader,
                 *args,
                 **kwargs):
        super(GoogleImageCrawler, self).__init__(
            feeder_cls, parser_cls, downloader_cls, *args, **kwargs)

    def crawl(self,
              keyword,
              offset=0,
              max_num=1000,
              date_min=None,
              date_max=None,
              min_size=None,
              max_size=None,
              language=None,
              img_type=None,
              img_color=None,
              usage_rights=None,
              file_idx_offset=0):
        if offset + max_num > 1000:
            if offset > 1000:
                self.logger.error(
                    '"Offset" cannot exceed 1000, otherwise you will get '
                    'duplicated searching results.')
                return
            elif max_num > 1000:
                max_num = 1000 - offset
                self.logger.warning(
                    'Due to Google\'s limitation, you can only get the first '
                    '1000 result. "max_num" has been automatically set to %d. '
                    'If you really want to get more than 1000 results, you '
                    'can specify different date ranges.', 1000 - offset)

        feeder_kwargs = dict(
            keyword=keyword,
            offset=offset,
            max_num=max_num,
            date_min=date_min,
            date_max=date_max,
            language=language,
            img_type=img_type,
            img_color=img_color,
            usage_rights=usage_rights)
        downloader_kwargs = dict(
            max_num=max_num,
            min_size=min_size,
            max_size=max_size,
            file_idx_offset=file_idx_offset)
        super(GoogleImageCrawler, self).crawl(
            feeder_kwargs=feeder_kwargs, downloader_kwargs=downloader_kwargs)
