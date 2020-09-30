import os
import os.path
import shlex
import subprocess

from pprint import pprint

import urllib.request
from urllib import request, parse
from urllib.parse import urlencode, quote_plus

from bs4 import BeautifulSoup

import html
import asyncio
import time

import youtube_dl
from youtube_search import YoutubeSearch

def shorten_url(url):
    data = { "url": url }
    tinyURL = 'https://tinyurl.com/api-create.php?url=' + url
    req = request.Request(
            "{}?{}".format(tinyURL,urlencode(data, quote_via=quote_plus)),
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
        }) # GET
    try:
        short = request.urlopen(req).read().decode('utf-8')
    except Exception as e:
        print("""

                """)
        print(url, e)
        print("""

                """)

        raise e
    print(short)
    return short

def extract_vid(url):
    return url[url.find('v=') + 2:]

def to_second(time):
    s = 0
    for l in map(int, time.split(':')):
        s = s * 60 + l
    return s

def playlist_by_id(list_id):
    """
    (title, yurl, aurl, duration)
    """
    playlist = []
    data = fetch_meta(url_by_list_id(list_id), vid=True)
    for _ in range(len(data) // 4):
        title, vid, aurl, duration, *data = data
        playlist.append((title, url_by_vid(vid), aurl, duration))
    if playlist:
        return playlist
    else:
        raise Exception ("Empty playlist or playlist not found")

class Logger(object):
    def __init__(self):
        self.data = []
    def debug(self, msg):
        _ = msg.split()
        if not any([msg.startswith('[download'),
                msg.startswith('[youtube'),
                msg.startswith('[info')]):
            self.data.append(msg)
        elif '[download] Downloading playlist:' in msg:
            YouTubePlugin.playListName = msg[len('[download] Downloading playlist: '):]
    def warning(self, msg):
        pass
    def error(self, msg):
        pass

def fetch_meta(url, vid=False):
    logger = Logger()
    ydl_opts = {
        'logger': logger,
        'simulate': True,
        'forceurl': True,
        'forcetitle': True,
        'forceduration': True,
        'quiet': True,
        'format': 'bestaudio/best'
    }
    if vid: ydl_opts['forceid'] = True
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return logger.data

def url_by_list_id(list_id):
    return 'https://www.youtube.com/playlist?list=' + list_id

def url_by_vid(vid):
    return 'https://www.youtube.com/watch?v=' + vid

def urls_by_term(textToSearch):
    results = YoutubeSearch(textToSearch, max_results=10).to_dict()
    return ['https://www.youtube.com' + e['url_suffix'] for e in results]

def url_by_term(textToSearch):
    try:
        c = urls_by_term(textToSearch)[0]
        return c
    except Exception as e:
        return []

def urls_by_url(url, classname, retry=True):
    print("search url is:", url)
    response = urllib.request.urlopen(url)
    html = response.read()
    soup = BeautifulSoup(html, 'html.parser')
    rtn = ['https://www.youtube.com' + vid['href']
            for vid in soup.findAll('a', href=True, attrs={'class': classname})
            if not vid['href'].startswith("https://")]
    if rtn: return rtn
    elif retry: urls_by_url(url, classname, False)
    else: raise Exception("No song found by the keyword QwQ")


cache_list = []
def next_url(url):
    rtn = urls_by_url(url, 'content-link spf-link yt-uix-sessionlink spf-link')
    # prevent repeat recommendation
    while len(rtn) > 1:
        if rtn[0] not in cache_list: break
        else: rtn.pop(0)
    return rtn[0]

if __name__ == '__main__':
    if not input("> test functions?").strip():
        """ put your test function here """
        print("test here")
    exit(0)

from .MusicPlugin import MusicPlugin, QueryState, Query_Type, Song, Playlist, Album

import soundcloud,logging, traceback, asyncio


class YouTubePlugin(MusicPlugin):
    NextGap = -1
    CONF_API_KEY = "sc_api_key"
    CONF_USE_SSL = "endpoint_use_ssl"
    lastSearch = ""
    enableAuto = False
    pendingMark = ''
    enableList = False
    lastLid = ''
    playListName = ''
    lastVid = ''
    lastPlay = None
    pendingList = []
    playlist = []
    playing = False
    delay = 2

    @staticmethod
    def name():
        return "YouTube"

    @staticmethod
    def help(wrapper):
        wrapper.reply_url('man page: ', 'https://gist.github.com/nobodyzxc/efe32e57d6fb5b07fccdcef27e947820')

    @staticmethod
    def status(wrapper):
        wrapper.reply_url("""playing: {}
enableAuto: {}
enableList: {}
pendingMark: {}
pendingList: {}
lastLid: {}
lastSearch:
""".format(YouTubePlugin.playing, YouTubePlugin.enableAuto, YouTubePlugin.enableList,
    YouTubePlugin.pendingMark, [x[1] if isinstance(x, tuple) else x for x in YouTubePlugin.pendingList], YouTubePlugin.lastLid),YouTubePlugin.lastSearch)


    @staticmethod
    def setLastPlay(song_info):
        YouTubePlugin.lastPlay = song_info
        cache_list.append(song_info[2])
        if len(cache_list) > 10:
            cache_list.pop(0)

    @staticmethod
    def search(keyword):
        yurl = url_by_term(keyword)
        data = fetch_meta(yurl)
        title, aurl, duration, *_ = data
        YouTubePlugin.lastSearch = yurl
        song = ('', title, yurl, shorten_url(aurl), to_second(duration))
        return song


    @staticmethod
    def play_search(keyword):
        try:
            song = YouTubePlugin.search(keyword)
        except Exception as e:
            YouTubePlugin.playing = False
            return '', '', '', '', str(e)

        YouTubePlugin.playing = True
        YouTubePlugin.setLastPlay(song)
        return YouTubePlugin.lastPlay

    @staticmethod
    def play(song):
        YouTubePlugin.playing = True
        YouTubePlugin.setLastPlay(song)
        return YouTubePlugin.lastPlay

    @staticmethod
    def stop_list(wrapper):
        YouTubePlugin.enableList = False
        YouTubePlugin.playlist = []
        wrapper.reply("stop playing playlist {}".format(YouTubePlugin.playListName))

    @staticmethod
    def clear_pending(wrapper):
        YouTubePlugin.pendingList = []
        wrapper.reply("pending list cleared")

    @staticmethod
    async def async_play_list(list_id, playlist, wrapper):
        if YouTubePlugin.enableList:
            wrapper.reply("stop playing playlist {}".format(YouTubePlugin.playListName))
            time.sleep(2)

        YouTubePlugin.lastLid = list_id
        YouTubePlugin.enableList = True
        if not playlist:
            wrapper.reply("playlist {} is empty".format(YouTubePlugin.playListName))
            return

        wrapper.reply("start playing playlist {}".format(YouTubePlugin.playListName))
        YouTubePlugin.playlist = playlist

    @staticmethod
    def play_list(list_id, wrapper):
        try:
            result = playlist_by_id(list_id)
        except Exception as e:
            wrapper.reply(str(e))
            return

        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        asyncio.get_event_loop().run_until_complete(
                YouTubePlugin.async_play_list(list_id, result, wrapper))

    @staticmethod
    async def async_pending_next(duration, playnext):
        mark = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        print("""
            pending {}
            """.format(mark))
        YouTubePlugin.pendingMark = mark
        time.sleep(duration)
        if YouTubePlugin.enableAuto \
                or YouTubePlugin.pendingList \
                or YouTubePlugin.enableList:
            #await asyncio.sleep(duration)
            if YouTubePlugin.pendingMark == mark:
                playnext()
            else:
                print("""
                    skip pending {} <> {}
                    """.format(YouTubePlugin.pendingMark, mark))
        else:
            if YouTubePlugin.pendingMark == mark:
                YouTubePlugin.playing = False
                print("Playing = False")

    @staticmethod
    def cur_pending_next(duration, playnext):
        mark = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        print("""
            pending {}
            """.format(mark))
        YouTubePlugin.pendingMark = mark
        time.sleep(duration)
        if YouTubePlugin.enableAuto \
                or YouTubePlugin.pendingList \
                or YouTubePlugin.enableList:
            if YouTubePlugin.pendingMark == mark:
                playnext()
            else:
                print("""
                skip pending {} <> {}
                """.format(YouTubePlugin.pendingMark, mark))
        else:
            if YouTubePlugin.pendingMark == mark:
                YouTubePlugin.playing = False
                print("Playing = False")


    @staticmethod
    def pending_next(duration, playnext):
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        asyncio.get_event_loop().run_until_complete(
                YouTubePlugin.async_pending_next(duration, playnext))

    @staticmethod
    def pending_keyword(keyword, play, reply):
        try:
            song = YouTubePlugin.search(keyword)
        except Exception as e:
            return reply(e)

        YouTubePlugin.pendingList.append(song)

        if YouTubePlugin.playing:
            reply('{} pended!'.format(song[1]))
        else:
            play()

    @staticmethod
    def pending_playlist(list_id, play, reply):
        YouTubePlugin.pendingList.append('list({})'.format(list_id))
        if YouTubePlugin.playing:
            reply('playlist {} pended!'.format(list_id))
        else:
            play()

    @staticmethod
    def pending_list(reply):
        if YouTubePlugin.pendingList or YouTubePlugin.playlist:
            reply('Pending:\n    '
                    + ('\n    list({} songs)\n   '.format(len(YouTubePlugin.playlist)) \
                            if YouTubePlugin.playlist else '')
                    + '\n   '.join(map(lambda s: s if len(s) < 21 else s[:15] + '...', [x[0] if isinstance(x, tuple) else x for x in YouTubePlugin.playlist]))
                    + ('\n    ' if YouTubePlugin.pendingList else '')
                    + '\n    '.join(map(lambda s: s if len(s) < 21 else s[:15] + '...', [x[1] if isinstance(x, tuple) else x for x in YouTubePlugin.pendingList])))
        else:
            reply('Empty Pending List')

    @staticmethod
    def next(wrapper):

        justList = False

        if YouTubePlugin.enableList:
            if YouTubePlugin.playlist:
                title, yurl, aurl, duration, *_ = YouTubePlugin.playlist.pop(0)
                YouTubePlugin.lastSearch = yurl
                time.sleep(YouTubePlugin.delay)
                YouTubePlugin.playing = True
                YouTubePlugin.setLastPlay(('List ', title, yurl, \
                        shorten_url(aurl), to_second(duration)))

                return YouTubePlugin.lastPlay
            else:
                YouTubePlugin.enableList = False
                justList = True
                wrapper.reply("play playlist {} done".format(YouTubePlugin.playListName))
                time.sleep(YouTubePlugin.delay)

        if YouTubePlugin.pendingList:
            song = YouTubePlugin.pendingList.pop(0)
            if isinstance(song, tuple):
                return YouTubePlugin.play(song)
            else:
                lid = song[len('list('):-1]
                YouTubePlugin.play_list(lid, wrapper)
                return YouTubePlugin.next(wrapper)

        # recommend next song
        elif YouTubePlugin.lastSearch and not justList:
            nurl = next_url(YouTubePlugin.lastSearch)

            data = fetch_meta(nurl)
            title, aurl, duration, *_ = data
            YouTubePlugin.lastSearch = nurl
            YouTubePlugin.playing = True
            YouTubePlugin.setLastPlay(('Next ', title, nurl, \
                    shorten_url(aurl), to_second(duration)))

            return YouTubePlugin.lastPlay

        else:
            YouTubePlugin.playing = False
            print("Playing = False")
            return "", "", "", "", 0
