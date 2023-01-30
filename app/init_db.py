import os
import psycopg2
from db_util.util import get_db_connection

conn = get_db_connection()

# Open a cursor to perform database operations
cur = conn.cursor()

# users table
cur.execute('DROP TABLE IF EXISTS users CASCADE;')
cur.execute('CREATE TABLE users ( user_id serial PRIMARY KEY,'
                                 'id varchar (200) UNIQUE,'
                                 'f_name varchar (150),'
                                 'l_name varchar (150),'
                                 'email varchar (150) UNIQUE NOT NULL);'
                                )

# Chat history table                                
cur.execute('DROP TABLE IF EXISTS chat_history;')
cur.execute('CREATE TABLE chat_history ( id serial PRIMARY KEY,'
                                 'user_id BIGINT REFERENCES users(user_id),'
                                 'query varchar (1500),'
                                 'response varchar (1500),'
                                 'time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,'
                                 'type VARCHAR(50) NOT NULL);'
                                )

                        

conn.commit()
cur.close()
conn.close()