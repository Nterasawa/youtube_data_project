document.addEventListener('DOMContentLoaded', function() {
    const searchButton = document.getElementById('search-button');
    const result = document.getElementById('result');
    const tabs = document.querySelectorAll('.tab');
    const popularVideos = document.getElementById('popular-videos');
    const latestVideos = document.getElementById('latest-videos');

    searchButton.addEventListener('click', performSearch);

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            if (tab.dataset.tab === 'popular') {
                popularVideos.style.display = 'flex';
                latestVideos.style.display = 'none';
            } else {
                popularVideos.style.display = 'none';
                latestVideos.style.display = 'flex';
            }
        });
    });

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
        document.getElementById('channel-icon').src = data.thumbnail;
        document.getElementById('channel-name').textContent = data.title;
        document.getElementById('channel-name').href = `https://www.youtube.com/channel/${data.id}`;
        document.getElementById('subscriber-count').textContent = `登録者数: ${formatNumber(data.subscriber_count)}`;
        document.getElementById('total-views').textContent = `総再生数: ${formatNumber(data.view_count)}`;
        document.getElementById('video-count').textContent = `動画数: ${formatNumber(data.video_count)}`;
        document.getElementById('channel-description').textContent = data.description;

        populateVideoList('popular-regular', data.videos.popular);
        populateVideoList('popular-shorts', data.videos.popular_shorts);
        populateVideoList('latest-regular', data.videos.latest);
        populateVideoList('latest-shorts', data.videos.latest_shorts);

        // 初期表示は人気順
        document.querySelector('.tab[data-tab="popular"]').click();

        result.classList.remove('hidden');
    }

    function populateVideoList(listId, videos) {
        const list = document.getElementById(listId);
        list.innerHTML = '';
        videos.forEach(video => {
            const li = document.createElement('li');
            li.innerHTML = `
                <img src="${video.snippet.thumbnails.medium.url}" alt="${video.snippet.title}">
                <div class="video-info">
                    <h4>${video.snippet.title}</h4>
                    <p>投稿日: ${formatDate(video.snippet.publishedAt)}</p>
                    <p>再生回数: ${formatNumber(video.statistics.viewCount || 0)}</p>
                </div>
            `;
            list.appendChild(li);
        });
    }

    function formatNumber(num) {
        return new Intl.NumberFormat('ja-JP').format(num);
    }

    function formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('ja-JP');
    }
});