import configparser
import logging
import os
import sys

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove, \
    CallbackQuery
from telegram.ext import CommandHandler, MessageHandler, Updater, CallbackContext, Filters, CallbackQueryHandler
from channel_message import ChannelMessage
import sqlite3

# logger init
log_format = '%(asctime)s; %(levelname)s; %(message)s'
logging.basicConfig(filename='logbook.log', level=logging.INFO, format=log_format)
logging.getLogger('deepl').setLevel(logging.ERROR)

thread_pool = {}


def start(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to use Rome Bus Monitor robot!\n"
                                                                    "About how to use this Bot:\n"
                                                                    "https://github.com/garryde/AtacBot/blob/master/DemoBot.md")


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
    if thread is None:
        result = "You don't have active monitor!"
    elif not thread.stop_flag:
        result = "You don't have active monitor!"
    else:
        result = "You have an active monitor!"
    update.message.reply_text(result)


def echo(update: Update, context: CallbackContext, notification: bool = False):
    thread = ChannelMessage(update, context, notification)
    thread.start()

    thread_p: ChannelMessage = thread_pool.get(update.effective_chat.id)
    if thread_p is not None:
        thread_p.stop_flag = False
    thread_pool[update.effective_chat.id] = thread


def notify(update: Update, context: CallbackContext):
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
            sql_insert = "INSERT INTO favorites (CHAT_ID, STOP, NOTE) VALUES ('" + chat_id + "', '" + arg[0] + "','" + arg[1] + "' )"
            c.execute(sql_insert)
            db_connection.commit()
            update.message.reply_text("Insert data successful!")
        else:
            sql_update = "UPDATE favorites set NOTE = '" + arg[1] + "' where CHAT_ID='" + chat_id +"' and STOP='" + arg[0] + "'"
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
        db_connection.commit()
    except sqlite3.OperationalError:
        pass
    return db_connection


if __name__ == '__main__':
    db_connection = get_database()

    updater = Updater(get_token(), use_context=True)
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("stop", stop))
    dp.add_handler(CommandHandler("check", check))
    dp.add_handler(CommandHandler("notify", notify))
    dp.add_handler(CommandHandler("getfavorites", get_favorites))
    dp.add_handler(CommandHandler("setfavorites", set_favorites))
    dp.add_handler(CommandHandler("delfavorites", del_favorites))
    dp.add_handler(CallbackQueryHandler(button))  # handling inline buttons pressing
    dp.add_handler(MessageHandler(Filters.text & (~Filters.command), echo))
    dp.add_handler(MessageHandler(Filters.command, unknown))
    # Log system started
    logging.info('System start successfully!')
    # Start the Bot
    updater.start_polling()
    updater.idle()
