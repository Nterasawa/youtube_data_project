import sqlite3
from datetime import datetime

def get_db_connection():
    conn = sqlite3.connect('youtube_data.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS channels (
            channel_id TEXT PRIMARY KEY,
            title TEXT,
            description TEXT,
            subscriber_count INTEGER,
            view_count INTEGER,
            video_count INTEGER,
            thumbnail TEXT,
            custom_url TEXT,
            published_at TEXT,
            last_updated DATETIME
        )
    ''')
    conn.commit()
    conn.close()

def insert_or_update_channel(channel_data):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT OR REPLACE INTO channels
        (channel_id, title, description, subscriber_count, view_count, video_count, thumbnail, custom_url, published_at, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    ''', (channel_data['channel_id'], channel_data['title'], channel_data['description'],
          channel_data['subscriber_count'], channel_data['view_count'], channel_data['video_count'],
          channel_data['thumbnail'], channel_data.get('custom_url', ''), channel_data['published_at'])
    )
    conn.commit()
    conn.close()

def get_channel_data(channel_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM channels WHERE channel_id = ?', (channel_id,))
    channel = cur.fetchone()
    conn.close()
    if channel:
        return dict(channel)
    return None