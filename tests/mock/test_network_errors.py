"""Mock tests for network error handling"""

import pytest
from unittest.mock import patch, MagicMock
from youtube_downloader.downloader import YouTubeDownloader
import requests


class TestNetworkErrors:
    """Mock tests for network error scenarios"""

    @patch('youtube_downloader.downloader.requests.post')
    def test_api_request_timeout(self, mock_post):
        """Test handling of API request timeouts"""
        mock_post.side_effect = requests.exceptions.Timeout("Connection timed out")

        downloader = YouTubeDownloader("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        with pytest.raises(Exception, match="Failed to fetch video info"):
            downloader._get_video_info()

    @patch('youtube_downloader.downloader.requests.post')
    def test_api_request_connection_error(self, mock_post):
        """Test handling of connection errors"""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")

        downloader = YouTubeDownloader("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        with pytest.raises(Exception, match="Failed to fetch video info"):
            downloader._get_video_info()

    @patch.object(YouTubeDownloader, 'get_formats')
    @patch('youtube_downloader.downloader.requests.Session.get')
    def test_download_request_timeout(self, mock_get, mock_get_formats):
        """Test handling of download request timeouts"""
        mock_get_formats.return_value = [{
            'itag': 22,
            'quality': '720p',
            'has_video': True,
            'has_audio': True,
            'url': 'http://example.com/video.mp4'
        }]

        mock_get.side_effect = requests.exceptions.Timeout("Download timed out")

        downloader = YouTubeDownloader("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        with pytest.raises(requests.exceptions.Timeout):
            downloader.download()

    @patch.object(YouTubeDownloader, 'get_formats')
    @patch('youtube_downloader.downloader.requests.Session.get')
    def test_download_connection_error(self, mock_get, mock_get_formats):
        """Test handling of download connection errors"""
        mock_get_formats.return_value = [{
            'itag': 22,
            'quality': '720p',
            'has_video': True,
            'has_audio': True,
            'url': 'http://example.com/video.mp4'
        }]

        mock_get.side_effect = requests.exceptions.ConnectionError("Connection lost")

        downloader = YouTubeDownloader("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        with pytest.raises(requests.exceptions.ConnectionError):
            downloader.download()

    @patch.object(YouTubeDownloader, 'get_formats')
    @patch('youtube_downloader.downloader.requests.Session.get')
    def test_download_http_error(self, mock_get, mock_get_formats):
        """Test handling of HTTP errors during download"""
        mock_get_formats.return_value = [{
            'itag': 22,
            'quality': '720p',
            'has_video': True,
            'has_audio': True,
            'url': 'http://example.com/video.mp4'
        }]

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        downloader = YouTubeDownloader("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        with pytest.raises(requests.exceptions.HTTPError):
            downloader.download()

    @patch('youtube_downloader.downloader.requests.post')
    def test_api_request_http_error(self, mock_post):
        """Test handling of HTTP errors in API requests"""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("403 Forbidden")
        mock_post.return_value = mock_response

        downloader = YouTubeDownloader("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        with pytest.raises(requests.exceptions.HTTPError):
            downloader._get_video_info()
