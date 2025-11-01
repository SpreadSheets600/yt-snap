"""Unit tests for URL parsing functionality"""

import pytest
from youtube_downloader.downloader import YouTubeDownloader


class TestURLParsing:
    """Test cases for YouTube URL parsing"""

    def test_extract_video_id_standard_url(self):
        """Test video ID extraction from standard YouTube URL"""
        downloader = YouTubeDownloader("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert downloader.video_id == "dQw4w9WgXcQ"

    def test_extract_video_id_short_url(self):
        """Test video ID extraction from youtu.be short URL"""
        downloader = YouTubeDownloader("https://youtu.be/dQw4w9WgXcQ")
        assert downloader.video_id == "dQw4w9WgXcQ"

    def test_extract_video_id_embed_url(self):
        """Test video ID extraction from embed URL"""
        downloader = YouTubeDownloader("https://www.youtube.com/embed/dQw4w9WgXcQ")
        assert downloader.video_id == "dQw4w9WgXcQ"

    def test_extract_video_id_with_params(self):
        """Test video ID extraction from URL with additional parameters"""
        downloader = YouTubeDownloader(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=30s"
        )
        assert downloader.video_id == "dQw4w9WgXcQ"

    def test_extract_video_id_direct_id(self):
        """Test video ID extraction when URL is just the video ID"""
        downloader = YouTubeDownloader("dQw4w9WgXcQ")
        assert downloader.video_id == "dQw4w9WgXcQ"

    def test_extract_video_id_invalid_url(self):
        """Test that invalid URLs raise ValueError"""
        with pytest.raises(ValueError):
            YouTubeDownloader("https://www.youtube.com/watch?v=invalid")

        with pytest.raises(ValueError):
            YouTubeDownloader("https://invalid.com/not@youtube")

        with pytest.raises(ValueError):
            YouTubeDownloader("not_a_url")

    def test_extract_video_id_edge_cases(self):
        """Test edge cases for video ID extraction"""
        downloader = YouTubeDownloader(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLxxx"
        )
        assert downloader.video_id == "dQw4w9WgXcQ"
        downloader = YouTubeDownloader("https://m.youtube.com/watch?v=dQw4w9WgXcQ")
        assert downloader.video_id == "dQw4w9WgXcQ"
