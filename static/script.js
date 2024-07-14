document.addEventListener('DOMContentLoaded', function() {
    const searchButton = document.getElementById('search-button');
    const result = document.getElementById('result');

    searchButton.addEventListener('click', performSearch);

    function performSearch() {
        const channelInput = document.getElementById('channel-input').value;
        const apiKey = document.getElementById('api-key').value;
        const openaiApiKey = document.getElementById('openai-api-key').value;

        fetch('/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `channel_input=${encodeURIComponent(channelInput)}&api_key=${encodeURIComponent(apiKey)}&openai_api_key=${encodeURIComponent(openaiApiKey)}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
            } else {
                displayResults(data);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while searching.');
        });
    }

    function displayResults(data) {
        // チャンネルヘッダーの設定
        const channelHeader = document.getElementById('channel-header');
        if (data.banner_url) {
            channelHeader.style.backgroundImage = `url(${data.banner_url})`;
            channelHeader.style.display = 'block';
        } else {
            channelHeader.style.display = 'none';
        }
    
        // チャンネルアイコンとリンクの設定
        const channelIcon = document.getElementById('channel-icon');
        channelIcon.src = data.thumbnail;
        
        const channelLink = document.getElementById('channel-link');
        channelLink.href = `https://www.youtube.com/channel/${data.channel_id}`;
    
        const channelNameElement = document.getElementById('channel-name');
        channelNameElement.textContent = data.title;
    
        document.getElementById('channel-id').textContent = `チャンネルID: ${data.channel_id}`;
        document.getElementById('subscriber-count').textContent = `登録者数: ${formatNumber(data.subscriber_count)}`;
        document.getElementById('total-views').textContent = `総再生数: ${formatNumber(data.view_count)}`;
        document.getElementById('video-count').textContent = `動画数: ${formatNumber(data.video_count)}`;
        document.getElementById('created-date').textContent = `チャンネル開設日: ${formatDate(data.published_at)}`;
        document.getElementById('channel-description').textContent = data.description;
    
        result.classList.remove('hidden');
    }

    function formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('ja-JP');
    }

    function formatNumber(num) {
        return new Intl.NumberFormat('ja-JP').format(num);
    }
});