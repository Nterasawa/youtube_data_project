document.addEventListener('DOMContentLoaded', function() {
    const searchButton = document.getElementById('search-button');
    const result = document.getElementById('result');

    searchButton.addEventListener('click', performSearch);

    function performSearch() {
        const channelInput = document.getElementById('channel-input').value;
        const apiKey = document.getElementById('api-key').value;

        fetch('/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `channel_input=${encodeURIComponent(channelInput)}&api_key=${encodeURIComponent(apiKey)}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error:', data.error);
                alert(data.error);
            } else {
                console.log('Received data:', data);
                displayResults(data.channel_info);
                setupVideoTabs(data.channel_info.channel_id, apiKey);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while searching. Check the console for more details.');
        });
    }

    function displayResults(channelInfo) {
        console.log('Displaying channel info:', channelInfo);
    
        // チャンネルヘッダーの設定
        const channelHeader = document.getElementById('channel-header');
        if (channelInfo.banner_url) {
            channelHeader.style.backgroundImage = `url(${channelInfo.banner_url})`;
            channelHeader.style.display = 'block';
        } else {
            channelHeader.style.display = 'none';
        }
    
        // チャンネルアイコンとリンクの設定
        const channelIcon = document.getElementById('channel-icon');
        channelIcon.src = channelInfo.thumbnail;
        
        const channelLink = document.getElementById('channel-link');
        channelLink.href = `https://www.youtube.com/channel/${channelInfo.channel_id}`;
    
        const channelNameElement = document.getElementById('channel-name');
        channelNameElement.textContent = channelInfo.title;
    
        document.getElementById('channel-id').textContent = `チャンネルID: ${channelInfo.channel_id}`;
        document.getElementById('subscriber-count').textContent = `登録者数: ${formatNumber(channelInfo.subscriber_count)}`;
        document.getElementById('total-views').textContent = `総再生数: ${formatNumber(channelInfo.view_count)}`;
        document.getElementById('video-count').textContent = `動画数: ${formatNumber(channelInfo.video_count)}`;
        document.getElementById('channel-description').textContent = channelInfo.description;
    
        result.classList.remove('hidden');
    }

    function setupVideoTabs(channelId, apiKey) {
        const videoTabs = document.getElementById('video-tabs');
        const videoList = document.getElementById('video-list');
        
        // タブボタンのイベントリスナーを設定
        videoTabs.querySelectorAll('button').forEach(button => {
            button.addEventListener('click', () => {
                const videoType = button.dataset.videoType;
                loadVideos(channelId, apiKey, videoType);
                
                // アクティブなタブを視覚的に示す
                videoTabs.querySelectorAll('button').forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
            });
        });
        
        // 初期表示として最新動画を表示
        const latestVideosButton = videoTabs.querySelector('button[data-video-type="latest_videos"]');
        latestVideosButton.click();
    }

    function loadVideos(channelId, apiKey, videoType) {
        fetch('/get_videos', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `channel_id=${encodeURIComponent(channelId)}&api_key=${encodeURIComponent(apiKey)}&video_type=${encodeURIComponent(videoType)}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error:', data.error);
                alert(data.error);
            } else {
                displayVideos(data.videos);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while loading videos. Check the console for more details.');
        });
    }

    function displayVideos(videos) {
        console.log('Displaying videos:', videos);
        const videoList = document.getElementById('video-list');
        videoList.innerHTML = ''; // リストをクリア
        
        if (videos && videos.length > 0) {
            videos.forEach(video => {
                const videoCard = createVideoCard(video);
                videoList.appendChild(videoCard);
            });
        } else {
            videoList.innerHTML = '<p>動画が見つかりませんでした。</p>';
        }
    }

    function createVideoCard(video) {
        const card = document.createElement('div');
        card.className = 'video-card';
        
        const link = document.createElement('a');
        link.href = `https://www.youtube.com/watch?v=${video.id}`;
        link.target = '_blank';
        
        const thumbnail = document.createElement('img');
        thumbnail.src = video.thumbnail;
        thumbnail.alt = video.title;
        
        const title = document.createElement('h3');
        title.textContent = video.title;
        
        const views = document.createElement('p');
        views.textContent = `再生回数: ${formatNumber(video.views)}`;
        
        const comments = document.createElement('p');
        comments.textContent = `コメント数: ${formatNumber(video.comments)}`;
        
        const publishDate = document.createElement('p');
        publishDate.textContent = `公開日: ${formatDate(video.publish_date)}`;
        
        link.appendChild(thumbnail);
        link.appendChild(title);
        card.appendChild(link);
        card.appendChild(views);
        card.appendChild(comments);
        card.appendChild(publishDate);
        
        return card;
    }

    function formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('ja-JP');
    }

    function formatNumber(num) {
        return new Intl.NumberFormat('ja-JP').format(num);
    }
});