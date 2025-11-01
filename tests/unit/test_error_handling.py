"""Unit tests for error handling functionality"""

import pytest
from unittest.mock import patch, MagicMock
import requests
from youtube_downloader.downloader import YouTubeDownloader


class TestErrorHandling:
    """Test cases for error handling"""

    def test_invalid_video_id_raises_error(self):
        """Test that invalid video IDs raise ValueError"""
        with pytest.raises(ValueError):
            YouTubeDownloader("invalid_id")

    @patch.object(YouTubeDownloader, '_get_video_info')
    def test_get_formats_unavailable_video(self, mock_get_info):
        """Test handling of unavailable videos"""
        mock_data = {
            'playabilityStatus': {
                'status': 'ERROR',
                'reason': 'Video unavailable'
            }
        }
        mock_get_info.return_value = mock_data

        downloader = YouTubeDownloader("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        with pytest.raises(Exception, match="Video not available: Video unavailable"):
            downloader.get_formats()

    @patch.object(YouTubeDownloader, '_get_video_info')
    def test_get_formats_no_formats_available(self, mock_get_info):
        """Test handling when no formats are available"""
        mock_data = {
            'playabilityStatus': {'status': 'OK'},
            'streamingData': {}
        }
        mock_get_info.return_value = mock_data

        downloader = YouTubeDownloader("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        with pytest.raises(Exception, match="No downloadable formats found"):
            downloader.download()

    @patch.object(YouTubeDownloader, 'get_formats')
    @patch('youtube_downloader.downloader.requests.Session.get')
    def test_download_invalid_quality(self, mock_get, mock_get_formats):
        """Test download with invalid quality raises exception"""
        mock_get_formats.return_value = [
            {
                'itag': 22,
                'quality': '720p',
                'has_video': True,
                'has_audio': True,
                'url': 'http://example.com/720p.mp4'
            }
        ]

        downloader = YouTubeDownloader("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        with pytest.raises(Exception, match="Quality invalid not found"):
            downloader.download(quality='invalid')

    @patch.object(YouTubeDownloader, 'get_formats')
    @patch('youtube_downloader.downloader.requests.Session.get')
    def test_download_invalid_itag(self, mock_get, mock_get_formats):
        """Test download with invalid itag raises exception"""
        mock_get_formats.return_value = [
            {
                'itag': 22,
                'quality': '720p',
                'has_video': True,
                'has_audio': True,
                'url': 'http://example.com/720p.mp4'
            }
        ]

        downloader = YouTubeDownloader("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        with pytest.raises(Exception, match="Format with itag 999 not found"):
            downloader.download(itag=999)

    @patch('youtube_downloader.downloader.requests.Session.post')
    def test_get_video_info_retries_on_failure(self, mock_post):
        """Test that _get_video_info retries on failure"""
        # First call fails, second succeeds
        mock_post.side_effect = [
            requests.exceptions.ConnectionError("Network error"),
            MagicMock(json=MagicMock(return_value={
                'playabilityStatus': {'status': 'OK'},
                'streamingData': {'formats': [], 'adaptiveFormats': []}
            }))
        ]

        downloader = YouTubeDownloader("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        # This should succeed after retry
        data = downloader._get_video_info()
        assert data['playabilityStatus']['status'] == 'OK'
        assert mock_post.call_count == 2
