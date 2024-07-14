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
    cur.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            video_id TEXT PRIMARY KEY,
            channel_id TEXT,
            title TEXT,
            thumbnail TEXT,
            views INTEGER,
            comments INTEGER,
            publish_date TEXT,
            last_updated DATETIME,
            FOREIGN KEY (channel_id) REFERENCES channels (channel_id)
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
          channel_data['thumbnail'], channel_data.get('custom_url', ''), channel_data.get('published_at', ''))
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

def insert_or_update_video(video_data):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT OR REPLACE INTO videos
        (video_id, channel_id, title, thumbnail, views, comments, publish_date, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
    ''', (video_data['id'], video_data['channel_id'], video_data['title'],
          video_data['thumbnail'], video_data['views'], video_data['comments'],
          video_data['publish_date'])
    )
    conn.commit()
    conn.close()

def get_videos(channel_id, video_type, limit=20):
    conn = get_db_connection()
    cur = conn.cursor()
    
    if video_type in ['latest_videos', 'latest_shorts']:
        order_by = 'publish_date DESC'
    else:
        order_by = 'views DESC'
    
    cur.execute(f'''
        SELECT * FROM videos
        WHERE channel_id = ?
        ORDER BY {order_by}
        LIMIT ?
    ''', (channel_id, limit))
    
    videos = [dict(row) for row in cur.fetchall()]
    conn.close()
    return videos