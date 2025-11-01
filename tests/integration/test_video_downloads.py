"""Integration tests for video download functionality"""

from unittest.mock import patch, MagicMock
from youtube_downloader.downloader import YouTubeDownloader


class TestVideoDownloads:
    """Integration tests for video download process"""

    @patch.object(YouTubeDownloader, 'get_formats')
    @patch('youtube_downloader.downloader.tqdm')
    @patch('youtube_downloader.downloader.requests.Session.get')
    def test_full_download_process(self, mock_get, mock_tqdm, mock_get_formats):
        """Test the complete download process from URL to file"""
        mock_get_formats.return_value = [
            {
                'itag': 22,
                'quality': '720p',
                'has_video': True,
                'has_audio': True,
                'url': 'http://example.com/video.mp4',
                'filesize': '1000000'
            }
        ]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': '1000000'}
        mock_response.iter_content.return_value = [b'data_chunk_1', b'data_chunk_2']
        mock_get.return_value = mock_response

        mock_bar = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_bar
        mock_tqdm.return_value.__exit__.return_value = None

        downloader = YouTubeDownloader("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        result = downloader.download(output_file='/tmp/integration_test.mp4')

        assert result == '/tmp/integration_test.mp4'
        mock_get.assert_called_once()
        assert mock_bar.update.call_count == 2

    @patch.object(YouTubeDownloader, 'get_formats')
    @patch('youtube_downloader.downloader.tqdm')
    @patch('youtube_downloader.downloader.requests.Session.get')
    def test_download_with_proxy_rotation(self, mock_get, mock_tqdm, mock_get_formats):
        """Test download with proxy rotation on failure"""
        from youtube_downloader.proxy_manager import ProxyManager

        mock_get_formats.return_value = [
            {
                'itag': 22,
                'quality': '720p',
                'has_video': True,
                'has_audio': True,
                'url': 'http://example.com/video.mp4'
            }
        ]

        # First call returns 429, second succeeds
        mock_response_429 = MagicMock()
        mock_response_429.status_code = 429
        mock_response_429.raise_for_status.side_effect = Exception("429")

        mock_response_ok = MagicMock()
        mock_response_ok.status_code = 200
        mock_response_ok.headers = {'content-length': '1000'}
        mock_response_ok.iter_content.return_value = [b'data']

        mock_get.side_effect = [mock_response_429, mock_response_ok]

        mock_bar = MagicMock()
        mock_tqdm.return_value.__enter__.return_value = mock_bar
        mock_tqdm.return_value.__exit__.return_value = None

        proxy_manager = MagicMock(spec=ProxyManager)
        proxy_manager.get_proxy.return_value = MagicMock()

        downloader = YouTubeDownloader("https://www.youtube.com/watch?v=dQw4w9WgXcQ", proxy_manager=proxy_manager)
        result = downloader.download(output_file='/tmp/proxy_test.mp4')

        assert result == '/tmp/proxy_test.mp4'
        assert mock_get.call_count == 2  # One failure, one success
