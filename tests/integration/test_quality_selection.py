"""Integration tests for quality selection functionality"""

from unittest.mock import patch, MagicMock
from youtube_downloader.downloader import YouTubeDownloader


class TestQualitySelection:
    """Integration tests for quality selection in downloads"""

    @patch.object(YouTubeDownloader, 'get_formats')
    @patch('youtube_downloader.downloader.tqdm')
    @patch('youtube_downloader.downloader.requests.Session.get')
    def test_quality_selection_priority(self, mock_get, mock_tqdm, mock_get_formats):
        """Test that quality selection follows priority: exact match > partial match > default"""
        mock_get_formats.return_value = [
            {
                'itag': 22,
                'quality': '720p',
                'has_video': True,
                'has_audio': True,
                'url': 'http://example.com/720p.mp4'
            },
            {
                'itag': 18,
                'quality': '360p',
                'has_video': True,
                'has_audio': True,
                'url': 'http://example.com/360p.mp4'
            },
            {
                'itag': 37,
                'quality': '1080p',
                'has_video': True,
                'has_audio': True,
                'url': 'http://example.com/1080p.mp4'
            }
        ]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': '1000000'}
        mock_response.iter_content.return_value = [b'data']
        mock_get.return_value = mock_response

        mock_bar = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_bar
        mock_tqdm.return_value.__exit__.return_value = None

        downloader = YouTubeDownloader("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        # Test exact quality match
        downloader.download(quality='720p', output_file='/tmp/720p.mp4')
        args, kwargs = mock_get.call_args
        assert '720p.mp4' in args[0]

        # Test partial match (should find 1080p for '1080')
        mock_get.reset_mock()
        downloader.download(quality='1080', output_file='/tmp/1080p.mp4')
        args, kwargs = mock_get.call_args
        assert '1080p.mp4' in args[0]

    @patch.object(YouTubeDownloader, 'get_formats')
    @patch('youtube_downloader.downloader.tqdm')
    @patch('youtube_downloader.downloader.requests.Session.get')
    def test_default_quality_selection(self, mock_get, mock_tqdm, mock_get_formats):
        """Test default quality selection when no quality specified"""
        mock_get_formats.return_value = [
            {
                'itag': 22,
                'quality': '720p',
                'has_video': True,
                'has_audio': True,
                'url': 'http://example.com/720p.mp4'
            },
            {
                'itag': 18,
                'quality': '360p',
                'has_video': True,
                'has_audio': True,
                'url': 'http://example.com/360p.mp4'
            },
            {
                'itag': 140,
                'quality': '128kbps',
                'has_video': False,
                'has_audio': True,
                'url': 'http://example.com/audio.mp4'
            }
        ]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': '1000000'}
        mock_response.iter_content.return_value = [b'data']
        mock_get.return_value = mock_response

        mock_bar = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_bar
        mock_tqdm.return_value.__exit__.return_value = None

        downloader = YouTubeDownloader("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        # Should select first format with both video and audio (720p)
        downloader.download(output_file='/tmp/default.mp4')
        args, kwargs = mock_get.call_args
        assert '720p.mp4' in args[0]
