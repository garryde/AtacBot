import configparser
import os
import sys


class Config:
    def __init__(self, file_name='config.ini', config_strs=[]):
        self.config_strs = config_strs
        self.file_name = file_name
        self.con = configparser.RawConfigParser()

        if not os.path.exists(file_name):
            self.con.add_section('config')
            for config_str in config_strs:
                if "list" in config_str:
                    self.con.set('config', config_str, '[]')
                else:
                    self.con.set('config', config_str, '')
            with open(file_name, 'w') as fw:
                self.con.write(fw)
            print("Running first time!")
            print('The configuration file has been generated!')
            print('Please fill configuration and run again!')
            sys.exit()
        self.con.read(file_name, encoding='utf-8')

    def read_str(self, config_key: str):
        val = dict(self.con.items('config'))[config_key]
        return 'empty' if val == "" else val

    def write_cookie(self, cookie: str):
        self.write_config('cookie', cookie)

    def write_config(self, config_key: str, config_val: str):
        current_val = self.read_str(config_key)
        if current_val == config_val:
            return
        self.con.set('config', config_key, config_val)
        with open(self.file_name, 'w') as fw:
            self.con.write(fw)
