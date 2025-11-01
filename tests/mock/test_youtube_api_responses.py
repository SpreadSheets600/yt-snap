"""Mock tests for YouTube API response handling"""

import pytest
from unittest.mock import patch, MagicMock
from youtube_downloader.downloader import YouTubeDownloader


class TestYouTubeAPIResponses:
    """Mock tests for YouTube API interactions"""

    @patch.object(YouTubeDownloader, '_get_video_info')
    def test_api_response_parsing_success(self, mock_get_info):
        """Test successful parsing of YouTube API response"""
        mock_data = {
            'playabilityStatus': {'status': 'OK'},
            'streamingData': {
                'formats': [
                    {
                        'itag': 22,
                        'qualityLabel': '720p',
                        'mimeType': 'video/mp4; codecs="avc1.64001F, mp4a.40.2"',
                        'url': 'https://example.com/video.mp4',
                        'contentLength': '1048576'
                    }
                ],
                'adaptiveFormats': []
            },
            'videoDetails': {
                'title': 'Test Video',
                'lengthSeconds': '300',
                'author': 'Test Channel'
            }
        }
        mock_get_info.return_value = mock_data

        downloader = YouTubeDownloader("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        formats = downloader.get_formats()

        assert len(formats) == 1
        assert formats[0]['itag'] == 22
        assert formats[0]['quality'] == '720p'
        assert 'https://example.com/video.mp4' in formats[0]['url']

    @patch.object(YouTubeDownloader, '_get_video_info')
    def test_api_response_private_video(self, mock_get_info):
        """Test handling of private/unavailable videos"""
        mock_data = {
            'playabilityStatus': {
                'status': 'ERROR',
                'reason': 'This video is private.'
            }
        }
        mock_get_info.return_value = mock_data

        downloader = YouTubeDownloader("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        with pytest.raises(Exception, match="Video not available: This video is private."):
            downloader.get_formats()

    @patch.object(YouTubeDownloader, '_get_video_info')
    def test_api_response_age_restricted(self, mock_get_info):
        """Test handling of age-restricted videos"""
        mock_data = {
            'playabilityStatus': {
                'status': 'ERROR',
                'reason': 'Sign in to confirm your age'
            }
        }
        mock_get_info.return_value = mock_data

        downloader = YouTubeDownloader("https://www.youtube.com/watch?v=age_restricted")

        with pytest.raises(Exception, match="Video not available: Sign in to confirm your age"):
            downloader.get_formats()

    @patch.object(YouTubeDownloader, '_get_video_info')
    def test_api_response_empty_formats(self, mock_get_info):
        """Test handling of videos with no available formats"""
        mock_data = {
            'playabilityStatus': {'status': 'OK'},
            'streamingData': {}
        }
        mock_get_info.return_value = mock_data

        downloader = YouTubeDownloader("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        formats = downloader.get_formats()

        assert formats == []

    @patch('youtube_downloader.downloader.requests.post')
    def test_api_request_structure(self, mock_post):
        """Test that API requests are structured correctly"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'playabilityStatus': {'status': 'OK'},
            'streamingData': {'formats': [], 'adaptiveFormats': []}
        }
        mock_post.return_value = mock_response

        downloader = YouTubeDownloader("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        downloader._get_video_info()

        # Verify the request was made correctly
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "https://www.youtube.com/youtubei/v1/player"

        payload = kwargs['json']
        assert payload['videoId'] == 'test'
        assert 'context' in payload
        assert payload['context']['client']['clientName'] == 'ANDROID'
