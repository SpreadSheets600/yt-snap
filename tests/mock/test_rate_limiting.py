"""Mock tests for rate limiting scenarios"""

import pytest
from unittest.mock import patch, MagicMock
from youtube_downloader.downloader import YouTubeDownloader
from youtube_downloader.proxy_manager import ProxyManager


class TestRateLimiting:
    """Mock tests for rate limiting and proxy rotation"""

    @patch.object(YouTubeDownloader, 'get_formats')
    @patch('youtube_downloader.downloader.requests.Session.get')
    def test_rate_limit_handling_with_proxy(self, mock_get, mock_get_formats):
        """Test rate limit handling with proxy rotation"""
        mock_get_formats.return_value = [{
            'itag': 22,
            'quality': '720p',
            'has_video': True,
            'has_audio': True,
            'url': 'http://example.com/video.mp4'
        }]

        # First request gets 429, second succeeds
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        mock_response_429.raise_for_status.side_effect = Exception("429 Too Many Requests")

        mock_response_ok = MagicMock()
        mock_response_ok.status_code = 200
        mock_response_ok.headers = {'content-length': '1000'}
        mock_response_ok.iter_content.return_value = [b'data']

        mock_get.side_effect = [mock_response_429, mock_response_ok]

        # Mock proxy manager
        proxy_manager = MagicMock(spec=ProxyManager)
        proxy1 = MagicMock()
        proxy2 = MagicMock()
        proxy_manager.get_proxy.side_effect = [proxy1, proxy2]

        downloader = YouTubeDownloader("https://www.youtube.com/watch?v=dQw4w9WgXcQ", proxy_manager=proxy_manager)

        with patch('youtube_downloader.downloader.tqdm'):
            result = downloader.download()

        assert result.endswith('video.mp4')
        assert mock_get.call_count == 2
        proxy_manager.record_failure.assert_called_once_with(proxy1, Exception("429 Too Many Requests"))
        proxy_manager.record_success.assert_called_once_with(proxy2)

    @patch.object(YouTubeDownloader, 'get_formats')
    @patch('youtube_downloader.downloader.requests.Session.get')
    def test_rate_limit_exhaustion(self, mock_get, mock_get_formats):
        """Test behavior when rate limiting persists despite proxy rotation"""
        mock_get_formats.return_value = [{
            'itag': 22,
            'quality': '720p',
            'has_video': True,
            'has_audio': True,
            'url': 'http://example.com/video.mp4'
        }]

        # All requests return 429
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = Exception("429 Too Many Requests")
        mock_get.return_value = mock_response

        proxy_manager = MagicMock(spec=ProxyManager)
        proxy_manager.get_proxy.return_value = MagicMock()

        downloader = YouTubeDownloader("https://www.youtube.com/watch?v=dQw4w9WgXcQ", proxy_manager=proxy_manager)

        with pytest.raises(Exception, match="Failed to get a successful response"):
            downloader.download()

    @patch('youtube_downloader.downloader.requests.post')
    def test_api_rate_limiting(self, mock_post):
        """Test rate limiting in API requests"""
        # Simulate rate limiting at API level
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = Exception("429 Too Many Requests")
        mock_post.return_value = mock_response

        downloader = YouTubeDownloader("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        with pytest.raises(Exception, match="Failed to fetch video info"):
            downloader._get_video_info()

    @patch.object(YouTubeDownloader, 'get_formats')
    @patch('youtube_downloader.downloader.requests.Session.get')
    def test_proxy_rotation_on_multiple_failures(self, mock_get, mock_get_formats):
        """Test proxy rotation continues on multiple consecutive failures"""
        mock_get_formats.return_value = [{
            'itag': 22,
            'quality': '720p',
            'has_video': True,
            'has_audio': True,
            'url': 'http://example.com/video.mp4'
        }]

        # Multiple 429 responses
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        mock_response_429.raise_for_status.side_effect = Exception("429 Too Many Requests")

        mock_response_ok = MagicMock()
        mock_response_ok.status_code = 200
        mock_response_ok.headers = {'content-length': '1000'}
        mock_response_ok.iter_content.return_value = [b'data']

        mock_get.side_effect = [mock_response_429, mock_response_429, mock_response_ok]

        proxy_manager = MagicMock(spec=ProxyManager)
        proxies = [MagicMock() for _ in range(3)]
        proxy_manager.get_proxy.side_effect = proxies

        downloader = YouTubeDownloader("https://www.youtube.com/watch?v=dQw4w9WgXcQ", proxy_manager=proxy_manager)

        with patch('youtube_downloader.downloader.tqdm'):
            result = downloader.download()

        assert result.endswith('video.mp4')
        assert mock_get.call_count == 3
        assert proxy_manager.record_failure.call_count == 2  # Two failures before success
        proxy_manager.record_success.assert_called_once_with(proxies[2])
