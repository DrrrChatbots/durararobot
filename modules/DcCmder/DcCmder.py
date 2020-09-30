from modules.module import Module
from decorators import *
from popyo import *
import functools
import time
import traceback
from pprint import pprint
import random
from datetime import datetime
import asyncio
import os
import discord
import threading

def run_it_forever(loop):
    loop.run_forever()

# DONE: allow drrr admins to do whatever they want

# !die for drrr_admins and gods to leave and hardkill the bot
# !givemehost for admins and gods
# !admin add username tripcode for admins and gods
# !admin remove username tripcode for admins (will not work on gods ofc)
# !givehost username
# !listadmins
# !leave
# !fjoin [roomid] (leaves and joins another room)
# !ban username
# !kick username
# !reportban username
# !unban username
# !asay [text]
# !toggledj
# !roomname [text]
# !roomdesc [text]

class DcClient(discord.Client):

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')
        self.home = self.get_channel(self.home)
        if self.sub: self.sub = self.get_channel(self.sub)
        if self.voice: self.voice = self.get_channel(self.voice)
        self.loop = asyncio.get_event_loop()
        if self.sub: await self.sub.send('ONLINE')
        else: await self.home.send('ONLINE')

    async def on_message(self, message):
        if message.author == self.user: return

        if self.sub:
            if message.channel.id == self.home.id:
                self.handle_chat(message)
            elif message.channel.id == self.sub.id:
                self.handle_cmd(message)
        else:
            if message.content.split()[0] in ['/room', '/user', '/lounge', '/join', '/give', '/leave ']:
                self.handle_cmd(message)
            else:
                self.handle_chat(message)

    async def direct_msg(self, user, message):
        if self.sub:
            await self.sub.send(message)
        else:
            channel = await user.create_dm()
            await channel.send(message)

    def send_msg(self, message, user = None):
        while isinstance(self.home, int):
            print("loop")
            pass
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # https://stackoverflow.com/questions/52232177/runtimeerror-timeout-context-manager-should-be-used-inside-a-task
            if user or message == 'not in room':
                asyncio.run_coroutine_threadsafe(self.direct_msg(user, message), self.loop)
            else:
                asyncio.run_coroutine_threadsafe(self.home.send(message), self.loop)
            return
            #loop = asyncio.new_event_loop()
            #asyncio.set_event_loop(loop)
        if user or message == 'not in room':
            loop.create_task(self.direct_msg(user, message))
        else:
            loop.create_task(self.home.send(message))

    async def play_music(self, user, title, url):
        message = '{} 放了音樂 [{}]({})'.format(user, title, url)
        await self.home.send(message)

        return

        if not self.voice: return

        if not self.vclient:
            self.vclient = await self.voice.connect()

        if not self.vclient.is_connected():
            await self.vclient.channel.connect()

        if await self.vclient.is_playing():
            await self.vclient.stop()

        await self.vclient.play(discord.FFmpegPCMAudio(url))

    async def stop_playing(self):
        await self.vclient.disconnect()

    def after_play(self, error=None):
        if error:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                asyncio.run_coroutine_threadsafe(self.stop_playing(), self.loop)
                return
            loop.create_task(self.stop_playing())

    def send_music(self, user, title, url):
        while isinstance(self.home, int):
            print("loop")
            pass

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            asyncio.run_coroutine_threadsafe(self.play_music(user, title, url), self.loop)
            return
        loop.create_task(self.play_music(user, title, url))


    def __init__(self, home, handle_chat, handle_cmd, voice = None, sub = None):
        super(DcClient, self).__init__()
        self.home = home
        self.handle_chat = handle_chat
        self.handle_cmd  = handle_cmd
        self.vclient = None
        self.voice = voice
        self.sub  = sub

class DcCmder(Module):

    def unload(self):
        pass
    def onjoin(self, conn_name, scrollback):
        self.sender.send_msg(self._config_mgr.cfg['connections'][conn_name]['username_incl_tripcode'].split('#')[0] + '已登入部屋')
        self.inRoom = True

    def onleave(self, conn_name):
        self.sender.send_msg(self._config_mgr.cfg['connections'][conn_name]['username_incl_tripcode'].split('#')[0] + '已離開部屋')
        self.inRoom = False

    @staticmethod
    def name():
        return "DcCmder"

    # @require_admin("You are not an admin!!")
    # @require_host("I'm not the host!!")
    # def _process_kick(self, wrapper, message):
    #     self.bot.kick()

    # todo: expose a neater interface; e.g. get_conn().is_host()

    @not_cli("How am I supposed to give you the host? :P")
    @require_admin("You are not an admin!!")
    @require_host("I'm not the host!!")
    def _givemehost(self, wrapper, message):
        self.bot.handover_host(wrapper._conn, message.sender.id)

    @require_admin("You are not an admin!!")
    @require_host("I'm not the host!!")
    def _givehost(self, wrapper, message):
        gave = False
        s = message.message.split()[-1]
        for key, user in wrapper.get_conn().room.users.items():
            if user.name == s:
                self.bot.handover_host(wrapper._conn, key)
                gave = True
                break
        if not gave:
            wrapper.reply("No one with that name is in the room.")

    @require_admin("You are not an admin!!")
    @require_host("I'm not the host!!")
    def _process_kick(self, wrapper, message):
        kicked = False
        s = message.message.split()[-1]
        for key, user in wrapper.get_conn().room.users.items():
            if user.name == s:
                self.bot.kick(wrapper._conn, key)
                kicked = True
                break
        if not kicked:
            wrapper.reply("No one with that name is in the room.")

    # certain functions will be called twice because sometimes the json.php polling returns duplicate messages:
    # https://pastebin.com/0TrgyX2n
    @require_admin("You are not an admin!!")
    @require_host("I'm not the host!!")
    def _process_ban(self, wrapper, message):
        banned = False
        s = message.message.split()[-1]
        for key, user in wrapper.get_conn().room.users.items():
            if user.name == s:
                self.bot.ban(wrapper._conn, key)
                banned = True
                break

        # if not banned:
        #     wrapper.reply("No one with that name is in the room.")

    @require_admin("You are not an admin!!")
    @require_host("I'm not the host!!")
    def _process_report_and_ban(self, wrapper, message):
        banned = False
        s = message.message.split()[-1]
        for key, user in wrapper.get_conn().room.users.items():
            if user.name == s:
                self.bot.report_and_ban(wrapper._conn, key)
                banned = True
                break
        if not banned:
            wrapper.reply("No one with that name is in the room.")

    @require_admin("You are not an admin!!")
    @require_host("I'm not the host!!")
    def _process_unban(self, wrapper, message):
        id = message.message.split()[-1]
        if id in wrapper.get_conn().room.banned_ids:
            self.bot.unban(wrapper._conn, id)
        else:
            wrapper.reply("Do !listbans to see a list of banned uids")

    @require_admin("You are not an admin!!")
    def _process_leave(self, wrapper, message):
        self.bot.leave(wrapper._conn)

    @require_admin("You are not an admin!!")
    def _process_reloadcfg(self, wrapper, message):
        self.bot.reload_cfg()
        wrapper.reply("Reloaded config.")

    @require_admin("You are not an admin!!")
    def _process_asay(self, wrapper, message):
        self.bot.send(wrapper._conn, message.message[6: ])

    @require_admin("You are not an admin!!")
    @require_host("I'm not the host!!")
    def _process_toggledj(self, wrapper, message):
        self.bot.set_dj_mode(wrapper._conn, not wrapper.get_conn().room.dj_mode)

    @require_admin("You are not an admin!!")
    @require_host("I'm not the host!!")
    def _process_roomname(self, wrapper, message):
        self.bot.set_room_name(wrapper._conn, message.message[10:])

    @require_admin("You are not an admin!!")
    @require_host("I'm not the host!!")
    def _process_roomdesc(self, wrapper, message):
        self.bot.set_room_desc(wrapper._conn, message.message[10:])


    @require_admin("You are not an admin!")
    def _process_admin_add(self, wrapper, message):
        (username, tripcode) = message.message[11:].split()
        self.bot.perms_mgr.allow_admin(username, tripcode)
        wrapper.reply("Added " + username + "#" + tripcode + " into the admins list.")

    @require_dm(";) Admins are everywhere")
    @require_admin("You are not an admin!")
    def _process_listadmins(self, wrapper, message):
        blk = wrapper.get_perms_mgr().get_admin_block()
        if blk == []:
            wrapper.reply("No admins added.")
        else:
            s = "\n".join([n + "#" + tc for (n, tc) in blk])
            wrapper.reply(s)

    @require_dm(";) Gods are everywhere")
    @require_god("You are not an god!")
    def _process_listgods(self, wrapper, message):
        blk = wrapper.get_perms_mgr().get_gods_block()
        if blk == []:
            wrapper.reply("No gods added.")
        else:
            s = "\n".join([n + "#" + tc for (n, tc) in blk])
            wrapper.reply(s)

    @require_admin("You are not an admin!!")
    def _process_fjoin(self, wrapper, message):
        # first, check if the room ID actually exists. (Only works with public rooms for now!)
        r = self.bot.get_rooms(wrapper._conn)
        rooms = {}

        for x in r:
            rooms[x['id']] = x

        desired_room = message.message.split()[1]

        if desired_room not in rooms.keys():
            wrapper.reply("This room ID isn't in the list of public rooms")
        elif rooms[desired_room]['limit'] == len(rooms[desired_room]['users']):
            wrapper.reply("This room is full!!")
        else:
            self.bot.leave(wrapper._conn)
            # need to wait until the room status has really been updated, so can't just call join

    def _process_listusers(self, wrapper, message):
        s = ""
        room = wrapper.get_conn().room
        for key, user in room.users.items():
            s += "%s#%s %s" % (user.name, user.tripcode if user.tripcode is not None else "", user.device)
            s += '\n'

        wrapper.reply(s)
        self.sender.send_msg(s)

    def _process_banned(self, wrapper, message):
        room = wrapper.get_conn().room
        if room.banned_ids == set():
            wrapper.reply("No banned users.")

        else:
            s = ""
            for id in room.banned_ids:
                s += "%s" % (id)
                s += '\n'
            wrapper.reply(s)


    def _wait_onleave(self, conn, desired_room):
        time.sleep(1)
        self.bot.join(conn, desired_room)

    @staticmethod
    def check_cmd(cmd_string):
        # arg_split = cmd_string.split()
        # if arg_split[0] not in ['!die', '!givemehost', '!givehost', '!admin', '!leave',
        #                         '!join', '!ban', '!reportban', '!unban', '!asay', '!toggledj', '!roomname', '!roomdesc']:
        #     return Module.CMD_INVALID
        #
        # if arg_split[0] == "!admin ":
        #     i = len(arg_split)
        #     if i == 2:
        #         return Module.CMD_VALID if arg_split[1] in ['givemehost'] else Module.CMD_PARTIALLY_VALID
        #
        # return Module.CMD_INVALID
        return Module.CMD_VALID

    def handle_cmd(self, msg):
        try:
            if '/help' in msg.content:
                self.sender.send_msg(
"""```
command  [args]   description

/* sauce-disc */

/room                   display users
/user                   display users
/lounge  [lang]         show lounge
/join    [room id]      join room
/give    [name]         give host
/leave                  leave room

/* sauce-ctrl */

/dm      [name]         dm user
/url     [msg] [url]    send url msg
```""", msg.author)

            elif '/user' in msg.content or '/room' in msg.content:
                if not self.inRoom:
                    self.sender.send_msg('not in room')
                else:
                    room = self.bot.get_room(next(iter(self.bot.conn.keys())))
                    s = '{} {} {}\n'.format(room.name, room.desc, room.lang)
                    for key, user in room.users.items():
                        s += "%s#%s %s" % (user.name, user.tripcode if user.tripcode is not None else "", user.device)
                        s += '\n'
                    self.sender.send_msg(s, msg.author)
            elif '/lounge' in msg.content:
                lang = msg.content.split()
                lang = lang[-1] if len(lang) > 1 else None

                self.sender.send_msg("=========================", msg.author)
                total_room = ''
                room_details = self.bot.get_rooms(next(iter(self.bot.conn.keys())))
                print("-----------------------------------")
                try:
                    acc = 0
                    no = 0
                    for i in room_details:
                        # i['description'], datetime.fromtimestamp(int(i['since'])).strftime('%Y-%m-%d %H:%M:%S'),
                        try:
                            if not lang or lang in i['language'].lower():
                                acc += 1
                                no += 1
                                host = i.get('host', 'none')
                                if type(host) == dict: host = host.get('name', 'none')
                                usernames = ', '.join([name for name in [u if type(u) == str else str(u.get('name', str(u))) for u in i['users']] if name != host])
                                new_room = "{}\n{}. {}({}) {} \n @({}) {}\n\n".format(
                                        i['id'], no, i['name'], str(i['total']) + "/" + str(i['limit']), i['language'], host, usernames)
                                total_room += new_room
                                print('page:', no)
                        except Exception as e:
                            print(e, 'error =>>>>')
                            try:
                                host = i.get('host', 'none')
                                if type(host) != 'str': host = host.get('name', 'none')
                            except Exception as e:
                                print('again', e)

                        if acc > 10:
                            acc = 0
                            self.sender.send_msg(total_room, msg.author)
                            total_room = ''
                            time.sleep(1)
                    if acc and len(total_room):
                        self.sender.send_msg(total_room, msg.author)
                        time.sleep(1)
                    self.sender.send_msg("=========================", msg.author)
                except Exception as e:
                    print(e, '... something error')
                print("===================================")

            elif '/leave' in msg.content:
                if not self.inRoom:
                    self.sender.send_msg('not in room')
                else:
                    self.bot.leave(next(iter(self.bot.conn.keys())))
            elif '/join' in msg.content:
                if self.inRoom:
                    self.sender.send_msg('leave room first')
                else:
                    self.sender.send_msg('join...')
                    self.bot.join(next(iter(self.bot.conn.keys())), msg.content.split()[1])
            elif '/give' in msg.content:
                gave = False
                s = msg.content.split()[-1]
                for key, user in self.bot.get_room(next(iter(self.bot.conn.keys()))).users.items():
                    if user.name == s:
                        self.bot.handover_host(next(iter(self.bot.conn.keys())), key)
                        gave = True
                        break
                if not gave:
                    self.sender.send_msg("No one with that name is in the room.")
        except Exception as e:
            self.sender.send_msg(str(e))
            print(e)
            raise e


    def handle_chat(self, msg):
        try:
            if '/dm' in msg.content:
                if not self.inRoom:
                    self.sender.send_msg('not in room')
                else:
                    args = msg.content.split()
                    if len(args) >= 3:
                        _, user, *txt = args
                        users = {u.name: u.id for u \
                                in self.bot.get_room(next(iter(self.bot.conn.keys()))).users.values()}
                        if user in users:
                            self.bot.dm(next(iter(self.bot.conn.keys())), users[user], ' '.join(txt))
                        else:
                            self.sender.send_msg('user {} not found'.format(user))
                    else:
                        self.sender.send_msg('not enough operands')
            elif '/url' in msg.content:
                if not self.inRoom:
                    self.sender.send_msg('not in room')
                else:
                    full = msg.content.split()
                    if len(full) >= 3:
                        txt, url = ' '.join(full[1:-1]), full[-1]
                        self.bot.send_url(next(iter(self.bot.conn.keys())), txt, url)
                    else:
                        self.sender.send_msg('not enough operands')
            else:
                if not self.inRoom:
                    self.sender.send_msg('not in room')
                else:
                    self.bot.send(next(iter(self.bot.conn.keys())), msg.content)
                    #print("Message: ", msg.content, msg, msg.sender, msg.sender.name)
        except Exception as e:
            self.sender.send_msg(str(e))
            print(e)
            raise e

    def forward(self, message):
        if message.type in [Message_Type.message, Message_Type.dm, Message_Type.url, Message_Type.dm_url]:
            if message.sender.name != self._config_mgr.cfg['connections'][next(iter(self.bot.conn.keys()))]['username_incl_tripcode'].split('#')[0] \
                    or 'YouTube:' in message.message \
                    or 'OutLink:' in message.message:
                if message.type == Message_Type.message:
                    self.sender.send_msg('[{}]: {}'.format(message.sender.name, message.message))
                if message.type == Message_Type.dm:
                    self.sender.send_msg('({}): {}'.format(message.sender.name, message.message))
                if message.type == Message_Type.url:
                    self.sender.send_msg('[{}]: {} {}'.format(message.sender.name, message.message, message.url))
                if message.type == Message_Type.dm_url:
                    self.sender.send_msg('({}): {} {}'.format(message.sender.name, message.message, message.url))
            elif message.type == Message_Type.dm:
                self.sender.send_msg('(self): {}'.format(message.message))

        elif message.type == Message_Type.me:
            self.sender.send_msg('_{}_: {}'.format(message.sender.name, message.content))
        elif message.type == Message_Type.join:
            self.sender.send_msg('/* 歡迎詞 */\n{} 已登入部屋\n'.format(message.sender.name))
        elif message.type == Message_Type.leave:
            self.sender.send_msg('{} 已退出部屋'.format(message.sender.name))
        elif message.type == Message_Type.new_host:
            self.sender.send_msg('{} 成為新房主'.format(message.sender.name))
        elif message.type == Message_Type.new_description:
            self.sender.send_msg('房間敘述 {}'.format(message.description))
        elif message.type == Message_Type.system:
            self.sender.send_msg('系統 {}'.format(message.message))
        elif message.type == Message_Type.ban:
            self.sender.send_msg('{} 被 ban 了'.format(message.to))
        elif message.type == Message_Type.unban:
            self.sender.send_msg('{} 被解 ban 了'.format(message.to))
        elif message.type == Message_Type.kick:
            self.sender.send_msg('{} 被踢了'.format(message.to))
        elif message.type == Message_Type.music:
            #self.sender.send_msg('{} 放了音樂 {} \n{}'.format(message.sender.name, message.music_name, message.play_url))
            self.sender.send_music(message.sender.name, message.music_name, message.play_url)

    # admins can make the bot part, enforce rejoin if kicked... kick/ban others..

    def handler(self, conn_name, message):
        self.forward(message)

    async def start_receiver_loop(self):
        print("\n\nrun loop\n\n")
        await self.dc.start(self.conf['dc_token'])

    def __init__(self, config_mgr, perms_mgr, bot):
        super(DcCmder, self).__init__(config_mgr, perms_mgr, bot)

        self.inRoom = False

        self.dc = DcClient(self.conf['dc_channel'], self.handle_chat, self.handle_cmd, self.conf['dc_subchan'], self.conf['dc_subchan'])
        self.sender = self.dc


        loop = asyncio.get_event_loop()
        loop.create_task(self.start_receiver_loop())
        thread = threading.Thread(target=run_it_forever, args=(loop,))
        thread.start()
        #loop = self.get_new_event_loop("discord")
        #loop = asyncio.get_event_loop()
        #loop.create_task(self.start_receiver_loop())
        #asyncio.run_coroutine_threadsafe(self.start_receiver_loop(), loop=loop)
