import configparser
import logging
import os
import sys
from sqlite3 import IntegrityError
import config
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import CommandHandler, MessageHandler, Updater, CallbackContext, Filters, CallbackQueryHandler
from channel_message import ChannelMessage
import sqlite3

config_file_name = "config.ini"

thread_pool = {}

# logger init
log_format = '%(asctime)s; %(levelname)s; %(message)s'
logging.basicConfig(filename='logbook.log', level=logging.INFO, format=log_format)
logging.getLogger('deepl').setLevel(logging.ERROR)



def start(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to use Rome Bus Monitor robot!\n"
                                                                    "About how to use this Bot:\n"
                                                                    "https://bit.ly/3RR2A9R")
    insert_user(update)


def stop(update: Update, context: CallbackContext):
    thread: ChannelMessage = thread_pool.get(update.effective_chat.id)
    if thread is None:
        result = "You don't have active monitor!"
    elif not thread.stop_flag:
        result = "You don't have active monitor!"
    else:
        thread.stop_flag = False
        thread_pool.pop(update.effective_chat.id)
        result = "Monitor stopped!"
    update.message.reply_text(result)


def check(update: Update, context: CallbackContext):
    thread: ChannelMessage = thread_pool.get(update.effective_chat.id)
    print()
    if thread is None:
        result = "You don't have active monitor!"
    elif thread.is_alive():
        result = "You have an active monitor!"
    else:
        result = "You don't have active monitor!"
    update.message.reply_text(result)


def echo(update: Update, context: CallbackContext, notification: bool = False):
    insert_user(update)
    update_count(update)

    thread = ChannelMessage(update, context, notification)
    thread.start()

    thread_p: ChannelMessage = thread_pool.get(update.effective_chat.id)
    if thread_p is not None:
        thread_p.stop_flag = False
    thread_pool[update.effective_chat.id] = thread


def notify(update: Update, context: CallbackContext):
    if update.message.text == "/notify":
        update.message.reply_text(
            'Please enter the correct command!\n'
            'Format: /notify BUS_STOP_NUMBER\n'
            'For example: /notify 70240')
    else:
        echo(update, context, True)


def button(update: Update, context: CallbackContext):
    query: CallbackQuery = update.callback_query
    query.answer()
    echo(update, context, True)


def set_favorites(update: Update, context: CallbackContext):
    arg: list = context.args
    chat_id = str(update.effective_chat.id)
    if len(arg) != 2:
        update.message.reply_text(
            'Please enter the correct command!\n'
            'Format: /setfavorites BUS_STOP_NUMBER NOTE \n'
            'For example: /setfavorites 70240 Termini')
    else:
        c = db_connection.cursor()
        sql_select = "SELECT CHAT_ID, STOP from favorites where CHAT_ID='" + chat_id + "' AND STOP='" + arg[0] + "'"
        result = c.execute(sql_select).fetchone()
        if result == None:
            sql_insert = "INSERT INTO favorites (CHAT_ID, STOP, NOTE) VALUES ('" + chat_id + "', '" + arg[0] + "','" + \
                         arg[1] + "' )"
            c.execute(sql_insert)
            db_connection.commit()
            update.message.reply_text("Insert data successful!")
        else:
            sql_update = "UPDATE favorites set NOTE = '" + arg[1] + "' where CHAT_ID='" + chat_id + "' and STOP='" + \
                         arg[0] + "'"
            c.execute(sql_update)
            db_connection.commit()
            update.message.reply_text("Update data successful!")


def get_favorites(update: Update, context: CallbackContext):
    cursor = db_connection.execute(
        "SELECT CHAT_ID, STOP, NOTE from favorites where CHAT_ID=" + str(update.effective_chat.id))
    keyboard = []
    for row in cursor:
        keyboard.append([InlineKeyboardButton(row[1] + " - " + row[2], callback_data=row[1])])
    if len(keyboard) == 0:
        update.message.reply_text("You don't have any favorite bus stop!")
    else:
        update.message.reply_text('Choose a bus stop:', reply_markup=InlineKeyboardMarkup(keyboard))


def del_favorites(update: Update, context: CallbackContext):
    arg: list = context.args
    if len(arg) != 1:
        update.message.reply_text(
            'Please enter the correct command!\n'
            'Format: /delfavorites BUS_STOP_NUMBER \n'
            'For example: /delfavorites 70240')
    else:
        c = db_connection.cursor()
        sql_select = "SELECT CHAT_ID, STOP from favorites where CHAT_ID='" + str(
            update.effective_chat.id) + "' AND STOP='" + arg[0] + "'"
        result = c.execute(sql_select).fetchone()

        if result is None:
            update.message.reply_text("Bus stop does not exist in Favorites!")
        else:
            sql_delete = "DELETE from favorites where CHAT_ID='" + str(update.effective_chat.id) + "' AND STOP='" + arg[
                0] + "'"
            result = c.execute(sql_delete)
            db_connection.commit()
            update.message.reply_text("Bus stop delete successful!")


def get_count(update: Update, context: CallbackContext):
    if update.effective_chat.id != int(admin_chat_id):
        update.message.reply_text("You don't have permission!")
    else:
        cursor = db_connection.execute("SELECT FULL_NAME, COUNT from users")
        result = "Name  -  Count\n"
        for row in cursor:
            result += row[0] + " - " + str(row[1]) + "\n"
        update.message.reply_text(result)


def unknown(update: Update, context: CallbackContext):
    update.message.reply_text("Sorry, I didn't understand that command.")



def get_database():
    db_connection = sqlite3.connect('database.db', check_same_thread=False)
    try:
        c = db_connection.cursor()
        c.execute('''CREATE TABLE favorites
               (ID INTEGER PRIMARY KEY     autoincrement,
               CHAT_ID           TEXT    NOT NULL,
               STOP           TEXT    NOT NULL,
               NOTE            TEXT     NOT NULL);''')
        c.execute('''CREATE TABLE message_mode
               (ID INTEGER PRIMARY KEY     autoincrement,
               CHAT_ID           TEXT    NOT NULL,
               MODE            INT     NOT NULL);''')
        c.execute('''CREATE TABLE users
               (CHAT_ID TEXT PRIMARY KEY   ,
               FULL_NAME         TEXT    NOT NULL,
               USERNAME         TEXT    NOT NULL,
               IS_BOT           INTEGER    NOT NULL,
               IS_PREMIUM        TEXT    NOT NULL,
               LANGUAGE_CODE     TEXT    NOT NULL,
               COUNT            INTEGER     default 0);''')
        db_connection.commit()
    except sqlite3.OperationalError:
        pass
    return db_connection


def insert_user(update: Update):
    chat_id = update.effective_user.id
    full_name = update.effective_user.full_name
    username = update.effective_user.username
    is_bot = update.effective_user.is_bot
    try:
        is_premium = update.effective_user.is_premium
    except Exception:
        is_premium = "None"
    language_code = update.effective_user.language_code
    c = db_connection.cursor()
    sql_insert_user = "INSERT INTO users (CHAT_ID,FULL_NAME,USERNAME, IS_BOT,IS_PREMIUM,LANGUAGE_CODE) VALUES ('%s','%s','%s','%s','%s','%s');" % (
    chat_id, full_name,username ,is_bot, is_premium, language_code)
    try:
        c.execute(sql_insert_user)
    except IntegrityError:
        sql_update_user = "UPDATE users SET FULL_NAME = '%s',USERNAME = '%s',IS_BOT = '%s',IS_PREMIUM = '%s',LANGUAGE_CODE = '%s' WHERE CHAT_ID = '%s';" % (
        full_name, username, is_bot, is_premium, language_code, chat_id)
        c.execute(sql_update_user)
    finally:
        db_connection.commit()


def update_count(update: Update):
    chat_id = update.effective_user.id
    sql_update_count = "UPDATE users SET COUNT = COUNT+1 WHERE CHAT_ID = '%s';" % chat_id
    c = db_connection.cursor()
    c.execute(sql_update_count)
    db_connection.commit()


if __name__ == '__main__':
    # Database connection
    db_connection = get_database()

    # config
    config_list = ["bot_token", "admin_chat_id", "cookie"]
    conf = config.Config(config_strs=config_list)
    tg_token = conf.read_str("bot_token")
    admin_chat_id = conf.read_str("admin_chat_id")


    updater = Updater(tg_token, use_context=True)
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("stop", stop))
    dp.add_handler(CommandHandler("check", check))
    dp.add_handler(CommandHandler("notify", notify))
    dp.add_handler(CommandHandler("getfavorites", get_favorites))
    dp.add_handler(CommandHandler("setfavorites", set_favorites))
    dp.add_handler(CommandHandler("delfavorites", del_favorites))
    dp.add_handler(CommandHandler("getcount", get_count))
    dp.add_handler(CallbackQueryHandler(button))  # handling inline buttons pressing
    dp.add_handler(MessageHandler(Filters.text & (~Filters.command), echo))
    dp.add_handler(MessageHandler(Filters.command, unknown))
    # Log system started
    logging.info('System start successfully!')
    # Start the Bot
    updater.start_polling()
    updater.idle()
