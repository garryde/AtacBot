#!/usr/bin/python3
from telegram import Update
from telegram.ext import CallbackContext
import threading
import atac
import time
import logging
import traceback


class ChannelMessage(threading.Thread):
    def __init__(self, update: Update, context: CallbackContext, notification: bool = False, cycle: int = 10):
        threading.Thread.__init__(self)
        if update.message is not None:
            if len(update.message.entities) != 0:
                self.number = update.message.text[update.message.entities[0].length:]
            else:
                self.number = update.message.text
        else:
            self.number = update.callback_query.data
        self.chat_id = update.effective_chat.id
        self.context = context
        self.notification = notification
        self.message = None
        self.stop_flag = True
        self.no_info = 0
        self.count = 0
        self.sent = ''
        # Cycle interval(second)
        self.sleep_time = 20
        self.no_info_sleep_time = 30
        # Thread activated duration(minutes * 60seconds)
        self.cycle = cycle * 60

    def run(self):
        while self.stop_flag:
            try:
                thread_info = threading.Thread.getName(self)+"-"+str(self.count)
                try:
                    full_data = atac.get_full_data(self.number)
                except Exception as e:
                    logging.warning("get_full_data(); chet_id:"+str(self.chat_id)+"; "+thread_info + "; " + str(e))
                    time.sleep(self.sleep_time)
                    continue
                # no data from ATAC
                if atac.get_stop_name(full_data) == '':
                    if (self.no_info == 1 and self.count == 0) or (self.no_info == 60/self.sleep_time and self.count != 0):
                        result = "No bus information!"
                        self.no_info += 1
                    else:
                        self.no_info += 1
                        time.sleep(self.no_info_sleep_time)
                        continue
                # received data from ATAC
                else:
                    self.no_info = 0
                    # Splicing information
                    result = "🚏 " + atac.get_stop_name(full_data) + "\n" + atac.get_status(full_data)
                # send message
                if self.count == 0:
                    self.message = self.context.bot.send_message(chat_id=self.chat_id, text=result, timeout=2)
                    self.sent = result
                    time.sleep(self.sleep_time)
                    self.count += 1
                elif self.count < self.cycle / self.sleep_time:
                    if result != self.sent:
                        self.sent = result
                        if self.notification:
                            self.message = self.context.bot.send_message(chat_id=self.chat_id, text=result, timeout=2)
                        else:
                            self.message = self.context.bot.edit_message_text(chat_id=self.chat_id,
                                                                              message_id=self.message.message_id,
                                                                              text=result, timeout=2)
                    time.sleep(self.sleep_time)
                    self.count += 1
                else:
                    self.stop_flag = False
                    self.message = self.context.bot.send_message(chat_id=self.chat_id, text='Monitor stoped!', timeout=2)
                    break
            except Exception as e:
                self.stop_flag = False
                logging.error("thread error; chet_id:" + str(self.chat_id) + "; " + thread_info + "; " + traceback.format_exc())
