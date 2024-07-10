from flask import Flask, render_template, request, jsonify
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

app = Flask(__name__)

def get_channel_info(api_key, channel_input):
    youtube = build('youtube', 'v3', developerKey=api_key)
    
    try:
        search_response = youtube.search().list(
            q=channel_input,
            type='channel',
            part='id',
            maxResults=1
        ).execute()
        
        if 'items' in search_response:
            channel_id = search_response['items'][0]['id']['channelId']
        else:
            return None
        
        channel_response = youtube.channels().list(
            part='snippet,statistics',
            id=channel_id
        ).execute()

        if 'items' in channel_response:
            channel = channel_response['items'][0]
            
            videos = get_videos(youtube, channel_id)

            return {
                'id': channel_id,
                'title': channel['snippet']['title'],
                'description': channel['snippet']['description'],
                'subscriber_count': channel['statistics']['subscriberCount'],
                'view_count': channel['statistics']['viewCount'],
                'video_count': channel['statistics']['videoCount'],
                'thumbnail': channel['snippet']['thumbnails']['default']['url'],
                'videos': videos
            }
        else:
            return None
    except HttpError as e:
        print(f'An error occurred: {e}')
        return None

def get_videos(youtube, channel_id):
    videos = {
        'popular': [],
        'popular_shorts': [],
        'latest': [],
        'latest_shorts': []
    }

    # 通常の動画を取得
    video_response = youtube.search().list(
        channelId=channel_id,
        type='video',
        part='id,snippet',
        maxResults=50
    ).execute()

    # ショート動画を取得
    shorts_response = youtube.search().list(
        channelId=channel_id,
        type='video',
        videoDuration='short',
        part='id,snippet',
        maxResults=50
    ).execute()

    all_videos = video_response['items'] + shorts_response['items']

    # 動画の詳細情報（再生回数など）を取得（50件ずつ）
    video_ids = [item['id']['videoId'] for item in all_videos]
    video_stats = {}

    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i:i+50]
        video_details = youtube.videos().list(
            part='statistics',
            id=','.join(chunk)
        ).execute()
        video_stats.update({item['id']: item['statistics'] for item in video_details['items']})

    for item in video_response['items']:
        item['statistics'] = video_stats.get(item['id']['videoId'], {})
        videos['popular'].append(item)
        videos['latest'].append(item)

    for item in shorts_response['items']:
        item['statistics'] = video_stats.get(item['id']['videoId'], {})
        videos['popular_shorts'].append(item)
        videos['latest_shorts'].append(item)

    # 並び替え
    videos['popular'] = sorted(videos['popular'], key=lambda x: int(x['statistics'].get('viewCount', 0)), reverse=True)[:10]
    videos['popular_shorts'] = sorted(videos['popular_shorts'], key=lambda x: int(x['statistics'].get('viewCount', 0)), reverse=True)[:10]
    videos['latest'] = sorted(videos['latest'], key=lambda x: x['snippet']['publishedAt'], reverse=True)[:10]
    videos['latest_shorts'] = sorted(videos['latest_shorts'], key=lambda x: x['snippet']['publishedAt'], reverse=True)[:10]

    return videos

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    api_key = request.form['api_key']
    channel_input = request.form['channel_input']
    try:
        channel_info = get_channel_info(api_key, channel_input)
        if channel_info:
            return jsonify(channel_info)
        else:
            return jsonify({'error': f"Channel not found for input: {channel_input}"})
    except HttpError as e:
        return jsonify({'error': f"YouTube API error: {str(e)}"})
    except Exception as e:
        return jsonify({'error': f"An unexpected error occurred: {str(e)}"})

if __name__ == '__main__':
    app.run(debug=True)