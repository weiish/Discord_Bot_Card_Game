import mysql.connector
from mysql.connector import errorcode
import os
import re
from discord.ext import commands
import images
import cards
import tempfile
import random
import config

class SQL:
    def __init__(self, client):
        self.client = client
        self.connect()

    def connect(self):
        self.connection = mysql.connector.connect(
            host=config.host,
            user=config.user,
            passwd=config.passwd,
            database=config.database
        )
        print("Connected to {}".format(config.database))
        self.cursor = self.connection.cursor(buffered=True)
        print("Cursor initiated")

        self.connection2 = mysql.connector.connect(
            host=config.host,
            user=config.user,
            passwd=config.passwd,
            database=config.database2
        )
        print("Connected to {}".format(config.database2))
        self.cursor2 = self.connection2.cursor(buffered=True)
        print("Cursor initiated")
        
    def exec(self, sql_command_string, sql_command_args=None):
        #Do Logging Things Here
        #----------------------
        #----------------------
        if sql_command_args:
            self.cursor.execute(sql_command_string, sql_command_args)
        else:
            self.cursor.execute(sql_command_string)
        self.connection.commit()

    def sel(self, sql_query_string, sql_command_args=None):
        if sql_command_args:
            self.cursor.execute(sql_query_string, sql_command_args)
        else:
            self.cursor.execute(sql_query_string)
        return self.cursor

    def disconnect(self):
        self.cursor.close()
        self.connection.close()
        self.cursor2.close()
        self.connection2.close()
    
    def exec2(self, sql_command_string, sql_command_args=None):
        #Do Logging Things Here
        #----------------------
        #----------------------
        if sql_command_args:
            self.cursor2.execute(sql_command_string, sql_command_args)
        else:
            self.cursor2.execute(sql_command_string)
        self.connection2.commit()

    def sel2(self, sql_query_string, sql_command_args=None):
        if sql_command_args:
            self.cursor2.execute(sql_query_string, sql_command_args)
        else:
            self.cursor2.execute(sql_query_string)
        return self.cursor2

    def create_database(self, db_name):
        try:
            self.exec(
                "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(db_name))
        except mysql.connector.Error as err:
            print("Failed to create database: {}".format(err))
            exit(1)

def setup(client):
    client.add_cog(SQL(client))
