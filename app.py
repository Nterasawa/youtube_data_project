from flask import Flask, render_template, request, jsonify
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import openai
from database import create_tables, get_channel_data, insert_or_update_channel

app = Flask(__name__)

# OpenAI APIキーの設定
openai.api_key = None

# データベーステーブルの作成
create_tables()

def get_channel_info(api_key, channel_input):
    youtube = build('youtube', 'v3', developerKey=api_key)
    
    try:
        # チャンネルIDかカスタムURLかを判断
        if channel_input.startswith('UC'):
            channel_id = channel_input
        else:
            search_response = youtube.search().list(
                q=channel_input,
                type='channel',
                part='id',
                maxResults=1
            ).execute()
            
            if 'items' in search_response and search_response['items']:
                channel_id = search_response['items'][0]['id']['channelId']
            else:
                return None
        
        # データベースからチャンネル情報を取得
        channel_data = get_channel_data(channel_id)
        if channel_data:
            return channel_data
        
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
                'subscriber_count': channel['statistics']['subscriberCount'],
                'view_count': channel['statistics']['viewCount'],
                'video_count': channel['statistics']['videoCount'],
                'thumbnail': channel['snippet']['thumbnails']['default']['url'],
                'custom_url': channel['snippet'].get('customUrl', ''),
                'published_at': channel['snippet']['publishedAt'],
                'banner_url': channel['brandingSettings']['image'].get('bannerExternalUrl', '')
            }

            # データベースにチャンネル情報を保存
            insert_or_update_channel(channel_data)

            return channel_data
        else:
            return None
    except HttpError as e:
        print(f'An error occurred: {e}')
        return None

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    api_key = request.form['api_key']
    channel_input = request.form['channel_input']
    openai.api_key = request.form['openai_api_key']
    
    try:
        channel_data = get_channel_info(api_key, channel_input)
        if channel_data:
            return jsonify(channel_data)
        else:
            return jsonify({'error': f"Channel not found for input: {channel_input}"})
    except Exception as e:
        return jsonify({'error': f"An error occurred: {str(e)}"})



if __name__ == '__main__':
    app.run(debug=True)