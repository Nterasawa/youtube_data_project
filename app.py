from flask import Flask, render_template, request, jsonify
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
import traceback
from database import create_tables, get_channel_data, insert_or_update_channel, insert_or_update_video, get_videos
import re
from datetime import timedelta

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

def parse_duration(duration):
    match = re.match(r'PT(\d+H)?(\d+M)?(\d+S)?', duration)
    if not match:
        return 0
    
    hours = int(match.group(1)[:-1]) if match.group(1) else 0
    minutes = int(match.group(2)[:-1]) if match.group(2) else 0
    seconds = int(match.group(3)[:-1]) if match.group(3) else 0
    
    return timedelta(hours=hours, minutes=minutes, seconds=seconds).total_seconds()

def get_youtube_service(api_key):
    return build('youtube', 'v3', developerKey=api_key)

def extract_channel_identifier(url):
    patterns = [
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/channel\/([a-zA-Z0-9_-]+)',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/user\/([a-zA-Z0-9_-]+)',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/@([a-zA-Z0-9_-]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return url  # If no match, return the original input

def get_channel_id(youtube, channel_input):
    channel_input = extract_channel_identifier(channel_input)
    
    if channel_input.startswith('UC'):
        return channel_input
    
    try:
        search_response = youtube.search().list(
            q=channel_input,
            type='channel',
            part='id',
            maxResults=1
        ).execute()
        
        if 'items' in search_response and search_response['items']:
            return search_response['items'][0]['id']['channelId']
        else:
            return None
    except HttpError as e:
        logging.error(f"An HTTP error {e.resp.status} occurred: {e.content}")
        return None

def get_channel_info(youtube, channel_id):
    try:
        channel_response = youtube.channels().list(
            part='snippet,statistics,brandingSettings',
            id=channel_id
        ).execute()

        if 'items' in channel_response and channel_response['items']:
            channel = channel_response['items'][0]
            
            channel_data = {
                'channel_id': channel_id,
                'title': channel['snippet']['title'],
                'description': channel['snippet']['description'],
                'subscriber_count': channel['statistics'].get('subscriberCount', 0),
                'view_count': channel['statistics'].get('viewCount', 0),
                'video_count': channel['statistics'].get('videoCount', 0),
                'thumbnail': channel['snippet']['thumbnails']['default']['url'],
                'banner_url': channel['brandingSettings'].get('image', {}).get('bannerExternalUrl', ''),
                'published_at': channel['snippet'].get('publishedAt', '')  # Add this line
            }

            insert_or_update_channel(channel_data)
            return channel_data
        else:
            logging.error(f"No channel found for channel_id: {channel_id}")
            return None
    except Exception as e:
        logging.error(f"Error in get_channel_info: {str(e)}")
        logging.error(traceback.format_exc())
        return None
    
def get_video_list(youtube, channel_id, video_type, max_results=20):
    try:
        # チャンネルのアップロード済み動画プレイリストIDを取得
        channel_response = youtube.channels().list(
            part='contentDetails',
            id=channel_id
        ).execute()
        uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

        # すべての動画を取得
        all_videos = []
        next_page_token = None
        while len(all_videos) < 200:  # 最大200件の動画を取得
            playlist_response = youtube.playlistItems().list(
                part='snippet',
                playlistId=uploads_playlist_id,
                maxResults=50,
                pageToken=next_page_token
            ).execute()
            
            all_videos.extend(playlist_response['items'])
            next_page_token = playlist_response.get('nextPageToken')
            
            if not next_page_token:
                break

        # 動画IDのリストを作成
        video_ids = [item['snippet']['resourceId']['videoId'] for item in all_videos]

        # 動画の詳細情報を取得（50件ずつ）
        all_video_details = []
        for i in range(0, len(video_ids), 50):
            chunk = video_ids[i:i+50]
            videos_response = youtube.videos().list(
                part='snippet,statistics,contentDetails',
                id=','.join(chunk)
            ).execute()
            all_video_details.extend(videos_response['items'])

        # 動画情報をフィルタリングして整形
        videos = []
        for video in all_video_details:
            duration = video['contentDetails']['duration']
            duration_seconds = parse_duration(duration)
            is_short = duration_seconds <= 60

            video_data = {
                'id': video['id'],
                'title': video['snippet']['title'],
                'thumbnail': video['snippet']['thumbnails']['medium']['url'],
                'views': int(video['statistics'].get('viewCount', 0)),
                'comments': int(video['statistics'].get('commentCount', 0)),
                'publish_date': video['snippet']['publishedAt'],
                'channel_id': channel_id,
                'is_short': is_short
            }
            videos.append(video_data)
            insert_or_update_video(video_data)

        # 動画タイプに応じてフィルタリングとソート
        if video_type == 'latest_videos':
            filtered_videos = [v for v in videos if not v['is_short']]
            filtered_videos.sort(key=lambda x: x['publish_date'], reverse=True)
        elif video_type == 'popular_videos':
            filtered_videos = [v for v in videos if not v['is_short']]
            filtered_videos.sort(key=lambda x: x['views'], reverse=True)
        elif video_type == 'latest_shorts':
            filtered_videos = [v for v in videos if v['is_short']]
            filtered_videos.sort(key=lambda x: x['publish_date'], reverse=True)
        elif video_type == 'popular_shorts':
            filtered_videos = [v for v in videos if v['is_short']]
            filtered_videos.sort(key=lambda x: x['views'], reverse=True)
        else:
            filtered_videos = videos

        return filtered_videos[:max_results]
    except Exception as e:
        logging.error(f"Error in get_video_list: {str(e)}")
        logging.error(traceback.format_exc())
        return []

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    api_key = request.form['api_key']
    channel_input = request.form['channel_input']
    
    try:
        youtube = get_youtube_service(api_key)
        
        channel_id = get_channel_id(youtube, channel_input)
        if not channel_id:
            return jsonify({'error': f"Channel not found for input: {channel_input}"})

        # データベースからチャンネル情報を取得
        channel_data = get_channel_data(channel_id)
        if not channel_data:
            channel_data = get_channel_info(youtube, channel_id)

        if channel_data:
            return jsonify({'channel_info': channel_data})
        else:
            return jsonify({'error': f"Could not retrieve channel information for: {channel_input}"})
    except Exception as e:
        logging.error(f"Error in search: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({'error': f"An error occurred: {str(e)}"})

@app.route('/get_videos', methods=['POST'])
def get_videos():
    api_key = request.form['api_key']
    channel_id = request.form['channel_id']
    video_type = request.form['video_type']
    
    try:
        youtube = get_youtube_service(api_key)
        videos = get_video_list(youtube, channel_id, video_type)
        return jsonify({'videos': videos})
    except Exception as e:
        logging.error(f"Error in get_videos: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({'error': f"An error occurred: {str(e)}"})

if __name__ == '__main__':
    app.run(debug=True)