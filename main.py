#!/bin/env python3.6
import os
import bot
import json
import config_mgr
import datetime
from time import sleep
from datetime import datetime

if __name__ == "__main__":
    b = bot.bot(config_mgr.config_mgr())
    b.login('default')

    while True:
        try:
            room_details = b.get_rooms('default')

            if not len(room_details):
                b.login('default')
                room_details = b.get_rooms('default')

            now = datetime.now()
            filename = now.strftime("%m_%d_%Y@%H:%M:%S") + '.json'
            print('log {} rooms to {}'.format(str(len(room_details)), filename))
            with open(os.path.join('lounge', filename), 'w') as out:
                out.write(json.dumps(room_details))
            sleep(6 * 60)
        except Exception as e:
            print(e)
            sleep(6 * 60)

    #bot_cli = bot.BotCLI(b)
    #bot_cli.prompt  = "> "
    #bot_cli.cmdloop_with_keyboard_interrupt()
