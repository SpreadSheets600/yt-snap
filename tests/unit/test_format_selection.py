"""Unit tests for format selection functionality"""

from unittest.mock import patch, MagicMock
from youtube_downloader.downloader import YouTubeDownloader


class TestFormatSelection:
    """Test cases for format selection"""

    @patch.object(YouTubeDownloader, '_get_video_info')
    def test_get_formats(self, mock_get_info):
        """Test retrieving available formats"""
        mock_data = {
            'streamingData': {
                'formats': [
                    {
                        'itag': 22,
                        'qualityLabel': '720p',
                        'mimeType': 'video/mp4; codecs="avc1.64001F, mp4a.40.2"',
                        'url': 'http://example.com/video.mp4',
                        'contentLength': '1000000'
                    }
                ],
                'adaptiveFormats': [
                    {
                        'itag': 140,
                        'quality': '128kbps',
                        'mimeType': 'audio/mp4; codecs="mp4a.40.2"',
                        'url': 'http://example.com/audio.mp4',
                        'contentLength': '500000'
                    }
                ]
            }
        }
        mock_get_info.return_value = mock_data

        downloader = YouTubeDownloader("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        formats = downloader.get_formats()

        assert len(formats) == 2

        # Check video format
        video_fmt = next(f for f in formats if f['itag'] == 22)
        assert video_fmt['quality'] == '720p'
        assert video_fmt['mime'] == 'video/mp4'
        assert video_fmt['has_video'] is True
        assert video_fmt['has_audio'] is True
        assert video_fmt['filesize'] == '1000000'

        # Check audio format
        audio_fmt = next(f for f in formats if f['itag'] == 140)
        assert audio_fmt['quality'] == '128kbps'
        assert audio_fmt['mime'] == 'audio/mp4'
        assert audio_fmt['has_video'] is False
        assert audio_fmt['has_audio'] is True
        assert audio_fmt['filesize'] == '500000'

    @patch.object(YouTubeDownloader, 'get_formats')
    @patch('youtube_downloader.downloader.requests.Session.get')
    def test_download_format_selection_by_quality(self, mock_get, mock_get_formats):
        """Test format selection by quality in download method"""
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
            }
        ]

        mock_response = MagicMock()
        mock_response.headers = {'content-length': '1000000'}
        mock_response.iter_content.return_value = [b'dummy data']
        mock_get.return_value = mock_response

        downloader = YouTubeDownloader("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        downloader.download(quality='360p', output_file='/tmp/test.mp4')

        # Assert that the 360p URL was requested
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert args[0] == 'http://example.com/360p.mp4'
        assert kwargs['stream'] is True

    @patch.object(YouTubeDownloader, 'get_formats')
    @patch('youtube_downloader.downloader.requests.Session.get')
    def test_download_format_selection_by_itag(self, mock_get, mock_get_formats):
        """Test format selection by itag in download method"""
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
            }
        ]

        mock_response = MagicMock()
        mock_response.headers = {'content-length': '1000000'}
        mock_response.iter_content.return_value = [b'dummy data']
        mock_get.return_value = mock_response

        downloader = YouTubeDownloader("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        downloader.download(itag=22, output_file='/tmp/test.mp4')

        # Assert that the 720p URL was requested
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert args[0] == 'http://example.com/720p.mp4'
        assert kwargs['stream'] is True
