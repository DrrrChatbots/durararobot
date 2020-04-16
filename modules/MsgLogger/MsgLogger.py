from modules.module import Module
from decorators import *
from popyo import *
import functools
import time
import traceback
from pprint import pprint
import random
from datetime import datetime
from pytg import Telegram
from pytg.utils import coroutine
import asyncio
import os

class MsgLogger(Module):

    def unload(self):
        pass
    def onjoin(self, conn_name, scrollback):
        pass

    def onleave(self, conn_name):
        pass

    @staticmethod
    def name():
        return "MsgLogger"

    def handler(self, conn_name, message):
        self.log(message)

    def __init__(self, config_mgr, perms_mgr, bot):
        super(MsgLogger, self).__init__(config_mgr, perms_mgr, bot)
        self.logfile = open(datetime.now().strftime("log/%Y%m%d.log"), "a")
        
    def log(self, message):
        typelist = {
                Message_Type.message: 'msg',
                Message_Type.dm: 'dm',
                Message_Type.url: 'url',
                Message_Type.dm_url: 'dm_url',
        }

        if message.type in [Message_Type.message, Message_Type.dm, Message_Type.url, Message_Type.dm_url]:
            s = "{} {} {} {}{}\n".format(typelist[message.type],
                datetime.now().strftime("%Y%m%d%H%M"),
                repr(message.sender.name), repr(message.message),
                ' ' + repr(message.url) if message.type in [Message_Type.url, Message_Type.dm_url] else '')

        elif message.type == Message_Type.me:
            s = "{} {} {} {}\n".format('me',
                datetime.now().strftime("%Y%m%d%H%M"),
                repr(message.sender.name), repr(message.content))
        elif message.type == Message_Type.join:
            s = "{} {} {}\n".format('join',
                datetime.now().strftime("%Y%m%d%H%M"),
                repr(message.sender.name))
        elif message.type == Message_Type.leave:
            s = "{} {} {}\n".format('leave',
                datetime.now().strftime("%Y%m%d%H%M"),
                repr(message.sender.name))
        elif message.type == Message_Type.new_host:
            s = "{} {} {}\n".format('new_host',
                datetime.now().strftime("%Y%m%d%H%M"),
                repr(message.sender.name))
        elif message.type == Message_Type.new_description:
            s = "{} {} {} {}\n".format('new_desc',
                datetime.now().strftime("%Y%m%d%H%M"),
                repr(message.sender.name), repr(message.description))
        elif message.type == Message_Type.system:
            s = "{} {} {} {}\n".format('systm',
                datetime.now().strftime("%Y%m%d%H%M"),
                'admin', repr(message.message))
        elif message.type == Message_Type.ban:
            s = "{} {} {} {}\n".format('ban',
                datetime.now().strftime("%Y%m%d%H%M"),
                repr(message.sender.name), repr(message.to))
        elif message.type == Message_Type.unban:
            s = "{} {} {} {}\n".format('unban',
                datetime.now().strftime("%Y%m%d%H%M"),
                repr(message.sender.name), repr(message.to))
        elif message.type == Message_Type.kick:
            s = "{} {} {} {}\n".format('kick',
                datetime.now().strftime("%Y%m%d%H%M"),
                repr(message.sender.name), repr(message.to))
        elif message.type == Message_Type.music:
            s = "{} {} {} {} {} {} {}\n".format('music',
                datetime.now().strftime("%Y%m%d%H%M"),
                repr(message.sender.name), repr(message.music_name), repr(message.music_url), repr(message.play_url), repr(message.share_url))
        try:
            self.logfile.write(s)
        except Exception as e:
            print(e, message, message.type, '\n\n\n\n\n\n')
        self.logfile.flush()
