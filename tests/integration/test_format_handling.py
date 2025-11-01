"""Integration tests for format handling functionality"""

from unittest.mock import patch, MagicMock
from youtube_downloader.downloader import YouTubeDownloader


class TestFormatHandling:
    """Integration tests for format handling"""

    @patch.object(YouTubeDownloader, '_get_video_info')
    def test_format_parsing_combined_vs_adaptive(self, mock_get_info):
        """Test parsing of combined vs adaptive formats"""
        mock_data = {
            'playabilityStatus': {'status': 'OK'},
            'streamingData': {
                'formats': [
                    {
                        'itag': 22,
                        'qualityLabel': '720p',
                        'mimeType': 'video/mp4; codecs="avc1.64001F, mp4a.40.2"',
                        'url': 'http://example.com/combined.mp4',
                        'contentLength': '1000000'
                    }
                ],
                'adaptiveFormats': [
                    {
                        'itag': 137,
                        'qualityLabel': '1080p',
                        'mimeType': 'video/mp4; codecs="avc1.64001F"',
                        'url': 'http://example.com/video_only.mp4',
                        'contentLength': '500000'
                    },
                    {
                        'itag': 140,
                        'quality': '128kbps',
                        'mimeType': 'audio/mp4; codecs="mp4a.40.2"',
                        'url': 'http://example.com/audio.mp4',
                        'contentLength': '300000'
                    }
                ]
            }
        }
        mock_get_info.return_value = mock_data

        downloader = YouTubeDownloader("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        formats = downloader.get_formats()

        assert len(formats) == 3

        # Combined format
        combined = next(f for f in formats if f['itag'] == 22)
        assert combined['has_video'] is True
        assert combined['has_audio'] is True

        # Video-only adaptive
        video_only = next(f for f in formats if f['itag'] == 137)
        assert video_only['has_video'] is True
        assert video_only['has_audio'] is False

        # Audio-only adaptive
        audio_only = next(f for f in formats if f['itag'] == 140)
        assert audio_only['has_video'] is False
        assert audio_only['has_audio'] is True

    @patch.object(YouTubeDownloader, 'get_formats')
    @patch('youtube_downloader.downloader.tqdm')
    @patch('youtube_downloader.downloader.requests.Session.get')
    def test_format_fallback_selection(self, mock_get, mock_tqdm, mock_get_formats):
        """Test format selection fallback when preferred format unavailable"""
        # Only adaptive formats available
        mock_get_formats.return_value = [
            {
                'itag': 137,
                'quality': '1080p',
                'has_video': True,
                'has_audio': False,
                'url': 'http://example.com/video.mp4'
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

        # Should select first format (video-only) since no combined available
        downloader.download(output_file='/tmp/fallback.mp4')
        args, kwargs = mock_get.call_args
        assert 'video.mp4' in args[0]
