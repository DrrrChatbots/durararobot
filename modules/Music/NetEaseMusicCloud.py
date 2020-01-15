import os
import shlex
import subprocess
import json

from pprint import pprint
import urllib.request
from bs4 import BeautifulSoup

import html
from urllib import request, parse
from urllib.parse import urlencode, quote_plus
import asyncio

"""
intro: https://zhuanlan.zhihu.com/p/30246788
"""

def get_song_id(song_name):
    """
    https://api.imjad.cn/cloudmusic/?type=search&search_type=1&s=cocoon
    """
    data = {
            "type": "search",
            "search_type": "1",
            "s": song_name
            }
    url = 'https://api.imjad.cn/cloudmusic/'
    req = request.Request("{}?{}".format(url,urlencode(data, quote_via=quote_plus)),
            headers = {
                'Host': 'music.163.com',
                'Proxy-Connection': 'keep-alive',
                'Origin': 'http://music.163.com',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.8'
                #'User-Agent': \
                #'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36',
                #'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36(KHTML, like Gecko) Chrome/35.0.1916.138 Safari/537.36',
                #'User-agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:57.0)Gecko/20100101 Firefox/57.0',
                #'Host':'music.163.com',
                #'Referer':'https://music.163.com'
                }
            ) # GET
    #short = request.urlopen(req).read().decode('utf-8')
    print("{}?{}".format(url,urlencode(data, quote_via=quote_plus)))
    result = json.loads(request.urlopen(req).read().decode('utf-8'))
    try: 
        songs = result['result']['songs']
    except Exception as e:
        print(result, e)
        return []
    return [(o['name'], o['id']) for o in songs]

def get_song_url(song_id):
    """
    https://api.imjad.cn/cloudmusic/?type=song&id=28012031
    """
    data = {
            "type": "song",
            "id": song_id,
            }
    url = 'https://api.imjad.cn/cloudmusic/'
    req = request.Request("{}?{}".format(url,urlencode(data, quote_via=quote_plus)),
            headers={
                'User-Agent': \
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
        }) # GET
    #short = request.urlopen(req).read().decode('utf-8')
    result = json.loads(request.urlopen(req).read().decode('utf-8'))
    return result['data'][0]['url']

if __name__ == '__main__':
    get_song_id('薬師寺寛邦 般若心经')
    exit(0)

from .MusicPlugin import MusicPlugin, QueryState, Query_Type, Song, Playlist, Album
import soundcloud,logging, traceback, asyncio
class NetEaseMusicCloudPlugin(MusicPlugin):

    searchList = []

    @staticmethod
    def name():
        return "NetEaseCloudMusic"

    @staticmethod
    def search(keyword):
        if keyword.split()[-1].isdigit():
            ks = keyword.split()
            info = get_song_id(' '.join(ks[:-1]))[int(ks[-1])]
            return info[0], get_song_url(info[1])
        else:
            NetEaseMusicCloudPlugin.searchList = get_song_id(keyword)[:10]
            return NetEaseMusicCloudPlugin.searchList

    @staticmethod
    def select(idx):
        info = NetEaseMusicCloudPlugin.searchList[idx]
        return info[0], get_song_url(info[1])

