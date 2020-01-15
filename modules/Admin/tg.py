from pytg import Telegram

drrr = u'chat#xxxxxxxxx'
admin = u'user#xxxxxxxxx'

tg = Telegram(
	telegram="/usr/bin/telegram-cli",
	pubkey_file="~/.telegram-cli/tg-server.pub")
receiver = tg.receiver
sender = tg.sender

def toAdmin(msg):
    sender.send_msg(admin, msg)

def toDrrrChat(msg):
    sender.send_msg(drrr, msg)
