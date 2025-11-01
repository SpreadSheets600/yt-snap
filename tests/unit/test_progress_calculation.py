"""Unit tests for progress calculation functionality"""

from unittest.mock import patch, MagicMock
from youtube_downloader.downloader import YouTubeDownloader


class TestProgressCalculation:
    """Test cases for download progress calculation"""

    @patch.object(YouTubeDownloader, 'get_formats')
    @patch('youtube_downloader.downloader.tqdm')
    @patch('youtube_downloader.downloader.requests.Session.get')
    def test_download_progress_calculation(self, mock_get, mock_tqdm, mock_get_formats):
        """Test that download progress is calculated and updated correctly"""
        mock_get_formats.return_value = [
            {
                'itag': 22,
                'quality': '720p',
                'has_video': True,
                'has_audio': True,
                'url': 'http://example.com/video.mp4',
                'filesize': '3000'
            }
        ]

        # Mock the response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': '3000'}
        mock_response.iter_content.return_value = [b'chunk1', b'chunk2', b'chunk3']
        mock_get.return_value = mock_response

        # Mock tqdm
        mock_bar = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_bar
        mock_tqdm.return_value.__exit__.return_value = None

        downloader = YouTubeDownloader("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        downloader.download(output_file='/tmp/test_progress.mp4')

        # Check that tqdm was called with total=3000
        mock_tqdm.assert_called_once_with(
            desc="/tmp/test_progress.mp4 [720p]",
            total=3000,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{rate_fmt}, {elapsed}<{remaining}]'
        )

        # Check that bar.update was called for each chunk
        assert mock_bar.update.call_count == 3
        mock_bar.update.assert_any_call(6)  # len(b'chunk1') = 6
        mock_bar.update.assert_any_call(6)
        mock_bar.update.assert_any_call(6)

    @patch.object(YouTubeDownloader, 'get_formats')
    @patch('youtube_downloader.downloader.tqdm')
    @patch('youtube_downloader.downloader.requests.Session.get')
    def test_download_progress_without_content_length(self, mock_get, mock_tqdm, mock_get_formats):
        """Test progress calculation when content-length header is missing"""
        mock_get_formats.return_value = [
            {
                'itag': 22,
                'quality': '720p',
                'has_video': True,
                'has_audio': True,
                'url': 'http://example.com/video.mp4',
                'filesize': '5000'
            }
        ]

        # Mock the response without content-length
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}  # No content-length
        mock_response.iter_content.return_value = [b'data']
        mock_get.return_value = mock_response

        # Mock tqdm
        mock_bar = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_bar
        mock_tqdm.return_value.__exit__.return_value = None

        downloader = YouTubeDownloader("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        downloader.download(output_file='/tmp/test_no_length.mp4')

        # Check that tqdm was called with total from filesize
        mock_tqdm.assert_called_once_with(
            desc="/tmp/test_no_length.mp4 [720p]",
            total=5000,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{rate_fmt}, {elapsed}<{remaining}]'
        )
