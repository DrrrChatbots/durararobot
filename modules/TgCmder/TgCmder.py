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


class TgCmder(Module):

    def unload(self):
        pass
    def onjoin(self, conn_name, scrollback):
        self.sender.send_msg(self.tg_chat, self._config_mgr.cfg['connections'][conn_name]['username_incl_tripcode'].split('#')[0] + '已登入部屋')
        self.inRoom = True

    def onleave(self, conn_name):
        self.sender.send_msg(self.tg_chat, self._config_mgr.cfg['connections'][conn_name]['username_incl_tripcode'].split('#')[0] + '已離開部屋')
        self.inRoom = False

    @staticmethod
    def name():
        return "TgCmder"

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
        self.sender.send_msg(self.tg_chat, s)

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

    @coroutine
    def tg_loop(self):
        show_u = lambda u: '{}#{}'.format(u.name, u.tripcode) if u.tripcode else u.name
        while True:
            msg = (yield)

            try:
                if msg['sender']['username'] == self.conf['tg_bot_name'] or msg['sender']['username'][-3:].lower() == 'bot':
                    continue                
                sender_address = 'user#{}'.format(msg['sender']['peer_id'])
            except Exception as e:
                print('>>>>> 1. "{}" 2. "{}"'.format(e, msg))
           
            try:
                if msg['sender']['username'] != self.conf['tg_bot_name']:
                    if '/help' in msg.text:
                        self.sender.send_msg(sender_address,
"""command [args]   description
/room   \t      \t     \t\t\t\tdisplay users
/users  \t      \t     \t\t\t\tdisplay users
/lounge \t[lang]\t \t\t\t\tshow lounge
/join   \t[room id]\t\t\t\tjoin room
/give   \t[name]   \t\t\t\tgive host
/dm     \t[name]   \t\t\tdm user
/url    \t[msg]\t[url]\t\t\tsend url msg
/leave  \t      \t     \t\t\t\t\t  leave room
!time report
!time report stop""")
     
                    elif '/users' in msg.text or '/room' in msg.text:
                        if not self.inRoom:
                            self.sender.send_msg(sender_address, 'not in room')
                        else:
                            room = self.bot.get_room(next(iter(self.bot.conn.keys())))
                            s = '{} {} {}\n'.format(room.name, room.desc, room.lang)
                            for key, user in room.users.items():
                                s += "%s#%s %s" % (user.name, user.tripcode if user.tripcode is not None else "", user.device)
                                s += '\n'
                            self.sender.send_msg(sender_address, s)
                    elif '/lounge' in msg.text:
                        lang = msg.text.split()
                        lang = lang[-1] if len(lang) > 1 else None

                        self.sender.send_msg(sender_address, "=========================")
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
                                    self.sender.send_msg(sender_address, total_room)
                                    total_room = ''
                                    time.sleep(1)
                            if acc and len(total_room):
                                self.sender.send_msg(sender_address, total_room)
                                time.sleep(1)
                            self.sender.send_msg(sender_address, "=========================")
                        except Exception as e:
                            print(e, '... something error')
                        print("===================================")
                    else:

                        try:
                            if str(msg['receiver']['peer_id']) != self.tg_chat_id:
                                self.sender.send_msg('user#{}'.format(msg['sender']['peer_id']), 'only work on DrrrChat group')
                                print(')))))) {}"'.format(msg))
                                continue 
                        except Exception as e:
                            print('>>>>> 1. "{}" 2. "{}"'.format(e, msg))


                        if '/leave' in msg.text:
                            if not self.inRoom:
                                self.sender.send_msg(self.tg_chat, 'not in room')
                            else:
                                self.bot.leave(next(iter(self.bot.conn.keys())))
                        elif '/join' in msg.text:
                            if self.inRoom:
                                self.sender.send_msg(self.tg_chat, 'leave room first')
                            else:
                                self.sender.send_msg(self.tg_chat, 'join...')
                                self.bot.join(next(iter(self.bot.conn.keys())), msg.text.split()[1])
                        elif '/give' in msg.text:
                            gave = False
                            s = msg.text.split()[-1]
                            for key, user in self.bot.get_room(next(iter(self.bot.conn.keys()))).users.items():
                                if user.name == s:
                                    self.bot.handover_host(next(iter(self.bot.conn.keys())), key)
                                    gave = True
                                    break
                            if not gave:
                                self.sender.send_msg(self.tg_chat, "No one with that name is in the room.")
                        elif '/dm' in msg.text:
                            if not self.inRoom:
                                self.sender.send_msg(self.tg_chat, 'not in room')
                            else:
                                args = msg.text.split()
                                if len(args) >= 3:
                                    _, user, *txt = args
                                    users = {u.name: u.id for u \
                                            in self.bot.get_room(next(iter(self.bot.conn.keys()))).users.values()}
                                    if user in users:
                                        self.bot.dm(next(iter(self.bot.conn.keys())), users[user], ' '.join(txt))
                                    else:
                                        self.sender.send_msg(self.tg_chat, 'user {} not found'.format(user))
                                else:
                                    self.sender.send_msg(self.tg_chat, 'not enough operands')
                        elif '/url' in msg.text:
                            if not self.inRoom:
                                self.sender.send_msg(self.tg_chat, 'not in room')
                            else:
                                full = msg.text.split()
                                if len(full) >= 3:
                                    txt, url = ' '.join(full[1:-1]), full[-1]
                                    self.bot.send_url(next(iter(self.bot.conn.keys())), txt, url)
                                else:
                                    self.sender.send_msg(self.tg_chat, 'not enough operands')
                        else:
                            if not self.inRoom:
                                self.sender.send_msg(self.tg_chat, 'not in room')
                            else:
                                self.bot.send(next(iter(self.bot.conn.keys())), msg.text)
                                #print("Message: ", msg.text, msg, msg.sender, msg.sender.name)
            except Exception as e:
                self.sender.send_msg(self.tg_chat, str(e))
                print(e)

    def forward(self, message):
        if message.type in [Message_Type.message, Message_Type.dm, Message_Type.url, Message_Type.dm_url]:
            if message.sender.name != self._config_mgr.cfg['connections'][next(iter(self.bot.conn.keys()))]['username_incl_tripcode'].split('#')[0] \
                    or 'YouTube:' in message.message \
                    or 'OutLink:' in message.message:
                if message.type == Message_Type.message:
                    self.sender.send_msg(self.tg_chat, '[{}]: {}'.format(message.sender.name, message.message))
                if message.type == Message_Type.dm:
                    self.sender.send_msg(self.tg_chat, '({}): {}'.format(message.sender.name, message.message))
                if message.type == Message_Type.url:
                    self.sender.send_msg(self.tg_chat, '[{}]: {} {}'.format(message.sender.name, message.message, message.url))
                if message.type == Message_Type.dm_url:
                    self.sender.send_msg(self.tg_chat, '({}): {} {}'.format(message.sender.name, message.message, message.url))
            elif message.type == Message_Type.dm:
                self.sender.send_msg(self.tg_chat, '(self): {}'.format(message.message))

        elif message.type == Message_Type.me:
            self.sender.send_msg(self.tg_chat, '_{}_: {}'.format(message.sender.name, message.content))
        elif message.type == Message_Type.join:
            self.sender.send_msg(self.tg_chat, '/* 歡迎詞 */\n{} 已登入部屋\n'.format(message.sender.name))
        elif message.type == Message_Type.leave:
            self.sender.send_msg(self.tg_chat, '{} 已退出部屋'.format(message.sender.name))
        elif message.type == Message_Type.new_host:
            self.sender.send_msg(self.tg_chat, '{} 成為新房主'.format(message.sender.name))
        elif message.type == Message_Type.new_description:
            self.sender.send_msg(self.tg_chat, '房間敘述 {}'.format(message.description))
        elif message.type == Message_Type.system:
            self.sender.send_msg(self.tg_chat, '系統 {}'.format(message.message))
        elif message.type == Message_Type.ban:
            self.sender.send_msg(self.tg_chat, '{} 被 ban 了'.format(message.to))
        elif message.type == Message_Type.unban:
            self.sender.send_msg(self.tg_chat, '{} 被解 ban 了'.format(message.to))
        elif message.type == Message_Type.kick:
            self.sender.send_msg(self.tg_chat, '{} 被踢了'.format(message.to))
        elif message.type == Message_Type.music:
            self.sender.send_msg(self.tg_chat, '{} 放了音樂 {} \n{}'.format(message.sender.name, message.music_name, message.play_url))

    # admins can make the bot part, enforce rejoin if kicked... kick/ban others..

    def handler(self, conn_name, message):
        self.forward(message)

    async def start_receiver_loop(self):
        self.receiver.message(self.tg_loop())

    def __init__(self, config_mgr, perms_mgr, bot):
        super(TgCmder, self).__init__(config_mgr, perms_mgr, bot)

        self.inRoom = False

        cli_paths = ["/usr/bin/telegram-cli",
                "/usr/local/bin/telegram-cli",
                "telegram-cli" ]
        tg_cli_path = self.conf['tg_cli_path']

        while not os.path.isfile(tg_cli_path) and len(cli_paths):
            tg_cli_path = cli_paths.pop(0)

        if tg_cli_path != self.conf['tg_cli_path']:
            self.conf['tg_cli_path'] = tg_cli_path
            self.save_config()

        self.tg = Telegram(
        	telegram=tg_cli_path,
        	pubkey_file=self.conf['tg_key_path'])

        self.tg_chat = self.conf['tg_chat']
        self.tg_chat_id = self.tg_chat[self.tg_chat.index('#') + 1:]

        self.receiver = self.tg.receiver
        self.sender = self.tg.sender
        self.receiver.start()

        loop = self.get_new_event_loop("telegram")
        asyncio.run_coroutine_threadsafe(self.start_receiver_loop(), loop=loop)
