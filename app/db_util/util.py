import json
import os
import psycopg2
import psycopg2.extras
from enum import Enum

class ChatType(Enum):
    EVENT_TIME = 'event_time'
    EVENT_NAME = 'event_name'
    INVALID = 'invalid'

def get_db_connection():
    conn = psycopg2.connect(
                host="localhost",
                database=os.environ['DB_NAME'],
                user=os.environ['DB_USERNAME'],
                password=os.environ['DB_PASSWORD'])
    return conn


def get_user(id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
    cur.execute("select * from users where users.id='{}';".format(id))
    users = cur.fetchall()
    cur.close()
    conn.close()
    if len(users) == 0:
        print ("No user with same id: {} found".format(id))
        return None
    if len(users) > 1:
        print ("Many users with same id: {} found, returning first one".format(id))
    return dict(users[0])


def add_user(id, f_name, l_name, email):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO users (id, f_name, l_name, email)'
                    'VALUES (%s, %s, %s, %s)',
                    (id, f_name, l_name, email)
                    )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print ("Could not add user:{}".format(e))
        return False
    return True


def get_chat_history(user_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * from chat_history where user_id='{}' ORDER BY time;".format(user_id))
    chats = cur.fetchall()
    cur.close()
    conn.close()
    chats = [dict(chat) for chat in chats]

    for chat in chats:
        chat['time'] = str(chat['time'])
    return chats


def add_chat(user_id, query, response, type):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO chat_history (user_id, query, response, type)'
                        'VALUES (%s, %s, %s, %s)',
                        (user_id, query, response, type)
                        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print ("Could add to chat: {}".format(e))
        return False
    return True

    