#!/usr/bin/python3
from telegram import Update
from telegram.ext import CallbackContext
import threading
import atac
import time


class ChannelMessage(threading.Thread):
    def __init__(self, update: Update, context: CallbackContext, notification: bool = False):
        threading.Thread.__init__(self)
        if update.message != None:
            if len(update.message.entities) is not 0:
                self.number = update.message.text[update.message.entities[0].length:]
            else:
                self.number = update.message.text
        else:
            self.number = update.callback_query.data
        self.chat_id = update.effective_chat.id
        self.context = context
        self.notification = notification
        self.message = None
        self.flag = True
        self.no_info = False
        self.count = 0
        self.sent = ''
        # Cycle interval
        self.sleep_time = 15
        self.no_info_sleep_time = 5
        # Thread activated duration
        self.cycle = 15*60

    def run(self):
        while self.flag:
            print(threading.Thread.getName(self)+": "+str(self.count))
            full_data = atac.get_full_data(self.number)
            # No data from ATAC
            if atac.get_stop_name(full_data) == '':
                if self.no_info:
                    result = "No bus information!"
                    self.no_info = False
                else:
                    self.no_info = True
                    time.sleep(self.no_info_sleep_time)
                    continue
            # Received data from ATAC
            else:
                self.no_info = False
                # Splicing information
                result = "🚏 " + atac.get_stop_name(full_data) + "\n" + atac.get_status(full_data)
            if self.count == 0:
                self.message = self.context.bot.send_message(chat_id=self.chat_id, text=result)
                self.sent = result
                time.sleep(self.sleep_time)
                self.count += 1
            elif self.count < self.cycle/self.sleep_time:
                if result != self.sent:
                    self.sent = result
                    if self.notification:
                        self.message = self.context.bot.send_message(chat_id=self.chat_id, text=result)
                    else:
                        self.message = self.context.bot.edit_message_text(chat_id=self.chat_id, message_id=self.message.message_id, text=result)
                time.sleep(self.sleep_time)
                self.count += 1
            else:
                self.flag = False
                self.message = self.context.bot.send_message(chat_id=self.chat_id, text='Monitor stoped!')
