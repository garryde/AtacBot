import configparser
import logging
import os
import sys

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, \
    CallbackQuery
from telegram.ext import CommandHandler, MessageHandler, Updater, CallbackContext, Filters, CallbackQueryHandler
from channel_message import ChannelMessage
import sqlite3

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

thread_pool = {}


def start(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to use Rome Bus Monitor robot!")


def stop(update: Update, context: CallbackContext):
    thread: ChannelMessage = thread_pool.get(update.effective_chat.id)
    if thread is None:
        result = "You don't have active monitor!"
    elif not thread.flag:
        result = "You don't have active monitor!"
    else:
        thread.flag = False
        thread_pool.pop(update.effective_chat.id)
        result = "Monitor stopped!"
    update.message.reply_text(result)


def echo(update: Update, context: CallbackContext, notification: bool = False):
    thread = ChannelMessage(update, context, notification)
    thread.start()

    thread_p: ChannelMessage = thread_pool.get(update.effective_chat.id)
    if thread_p is not None:
        thread_p.flag = False
    thread_pool[update.effective_chat.id] = thread


def notify(update: Update, context: CallbackContext):
    echo(update, context, True)


def button(update: Update, context: CallbackContext):
    query: CallbackQuery = update.callback_query
    query.answer()
    echo(update, context, True)


def set_favorites(update: Update, context: CallbackContext):
    arg: list = context.args
    if len(arg) != 2:
        update.message.reply_text(
            'Please enter the correct command!\nFormat: /set_favorites BUS_STOP_NUMBER NOTE \nFor example: /set_favorites 70240 Termini')
    else:
        c = database_conn.cursor()
        sql = "INSERT INTO favorites (CHAT_ID, STOP, NOTE) VALUES ('"+str(update.effective_chat.id)+"', '"+arg[0]+"','"+arg[1]+"' )"
        c.execute(sql)
        database_conn.commit()
        update.message.reply_text("Insert or update data successful!")


def get_favorites(update: Update, context: CallbackContext):
    cursor = database_conn.execute(
        "SELECT CHAT_ID, STOP, NOTE from favorites where CHAT_ID=" + str(update.effective_chat.id))
    keyboard = []
    for row in cursor:
        keyboard.append([InlineKeyboardButton(row[1] + " - " + row[2], callback_data=row[1])])
    if len(keyboard) == 0:
        update.message.reply_text("You don't have any favorite bus stop!")
    else:
        update.message.reply_text('Choose a bus stop:', reply_markup=InlineKeyboardMarkup(keyboard))


def unknown(update: Update, context: CallbackContext):
    update.message.reply_text("Sorry, I didn't understand that command.")


def get_token() -> str:
    file_name = "config.ini"
    con = configparser.RawConfigParser()
    if not os.path.exists(file_name):
        con.add_section('config')
        con.set('config', "token", '')
        with open(file_name, 'w') as fw:
            con.write(fw)
        print("Running first time!")
        print('The configuration file has been generated!')
        print('Please insert Telegram Bot token!')
        sys.exit()
    con.read(file_name, encoding='utf-8')
    return dict(con.items('config'))["token"]


def get_database():
    database_conn = sqlite3.connect('database.db', check_same_thread=False)
    try:
        c = database_conn.cursor()
        c.execute('''CREATE TABLE favorites
               (ID INTEGER PRIMARY KEY     autoincrement,
               CHAT_ID           TEXT    NOT NULL,
               STOP           TEXT    NOT NULL,
               NOTE            TEXT     NOT NULL);''')
        c.execute('''CREATE TABLE message_mode
               (ID INTEGER PRIMARY KEY     autoincrement,
               CHAT_ID           TEXT    NOT NULL,
               MODE            INT     NOT NULL);''')
        database_conn.commit()
    except sqlite3.OperationalError:
        pass
    return database_conn


if __name__ == '__main__':
    database_conn = get_database()

    updater = Updater(get_token(), use_context=True)
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("stop", stop))
    dp.add_handler(CommandHandler("notify", notify))
    dp.add_handler(CommandHandler("getfavorites", get_favorites))
    dp.add_handler(CommandHandler("setfavorites", set_favorites))
    dp.add_handler(CallbackQueryHandler(button))  # handling inline buttons pressing
    dp.add_handler(MessageHandler(Filters.text & (~Filters.command), echo))
    dp.add_handler(MessageHandler(Filters.command, unknown))

    # Start the Bot
    updater.start_polling()
    updater.idle()
