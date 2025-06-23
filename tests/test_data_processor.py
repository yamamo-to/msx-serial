"""
Tests for data processor module
"""

from unittest.mock import Mock, patch
from msx_serial.core.data_processor import DataBuffer, DataProcessor
from msx_serial.protocol.msx_detector import MSXProtocolDetector


class TestDataBuffer:
    """Test DataBuffer class"""

    def setup_method(self):
        """Setup test"""
        self.buffer = DataBuffer()

    def test_init(self):
        """Test initialization"""
        assert self.buffer.buffer == ""
        assert self.buffer.last_update_time == 0.0

    def test_add_data(self):
        """Test adding data to buffer"""
        with patch("time.time", return_value=123.456):
            self.buffer.add_data("test data")
            assert self.buffer.buffer == "test data"
            assert self.buffer.last_update_time == 123.456

    def test_add_multiple_data(self):
        """Test adding multiple data chunks"""
        with patch("time.time", return_value=123.456):
            self.buffer.add_data("first")
            self.buffer.add_data(" second")
            assert self.buffer.buffer == "first second"

    def test_clear(self):
        """Test clearing buffer"""
        self.buffer.add_data("test")
        self.buffer.clear()
        assert self.buffer.buffer == ""

    def test_get_content(self):
        """Test getting buffer content"""
        self.buffer.add_data("content")
        assert self.buffer.get_content() == "content"

    def test_has_content_true(self):
        """Test has_content when buffer has content"""
        self.buffer.add_data("content")
        assert self.buffer.has_content() is True

    def test_has_content_false_empty(self):
        """Test has_content when buffer is empty"""
        assert self.buffer.has_content() is False

    def test_has_content_false_whitespace(self):
        """Test has_content when buffer has only whitespace"""
        self.buffer.add_data("   \n\t  ")
        assert self.buffer.has_content() is False

    def test_is_timeout_true(self):
        """Test timeout detection when timed out"""
        with patch("time.time", side_effect=[100.0, 101.5]):
            self.buffer.add_data("test")
            result = self.buffer.is_timeout(1.0)
            assert result is True

    def test_is_timeout_false(self):
        """Test timeout detection when not timed out"""
        with patch("time.time", side_effect=[100.0, 100.5]):
            self.buffer.add_data("test")
            result = self.buffer.is_timeout(1.0)
            assert result is False


class TestDataProcessor:
    """Test DataProcessor class"""

    def setup_method(self):
        """Setup test"""
        self.mock_detector = Mock(spec=MSXProtocolDetector)
        self.processor = DataProcessor(self.mock_detector)

    def test_init(self):
        """Test initialization"""
        assert self.processor.detector == self.mock_detector
        assert isinstance(self.processor.buffer, DataBuffer)

    def test_process_data_no_prompt(self):
        """Test processing data without prompt"""
        self.mock_detector.detect_prompt.return_value = False

        result = self.processor.process_data("test data")

        assert result == []
        assert self.processor.buffer.get_content() == "test data"

    def test_process_data_with_prompt(self):
        """Test processing data with prompt"""
        self.mock_detector.detect_prompt.return_value = True

        with patch.object(self.processor, "_split_prompt_data") as mock_split:
            mock_split.return_value = [("line1", False), ("A>", True)]

            result = self.processor.process_data("line1\nA>")

            assert result == [("line1", False), ("A>", True)]
            assert self.processor.buffer.get_content() == ""
            mock_split.assert_called_once()

    def test_check_timeout_no_timeout(self):
        """Test timeout check when no timeout"""
        self.processor.buffer.add_data("test")

        with patch.object(self.processor.buffer, "is_timeout", return_value=False):
            result = self.processor.check_timeout(0.1)
            assert result is None

    def test_check_timeout_with_timeout(self):
        """Test timeout check when timeout occurred"""
        self.processor.buffer.add_data("test")
        self.mock_detector.detect_prompt.return_value = True

        with (
            patch.object(self.processor.buffer, "is_timeout", return_value=True),
            patch.object(self.processor.buffer, "has_content", return_value=True),
        ):
            result = self.processor.check_timeout(0.1)

            assert result == ("test", True)
            assert self.processor.buffer.get_content() == ""

    def test_check_timeout_no_content(self):
        """Test timeout check when no content"""
        with patch.object(self.processor.buffer, "has_content", return_value=False):
            result = self.processor.check_timeout(0.1)
            assert result is None

    def test_check_prompt_candidate_success(self):
        """Test prompt candidate check success"""
        self.processor.buffer.add_data("A")
        self.mock_detector.is_prompt_candidate.return_value = True
        self.mock_detector.detect_prompt.return_value = True

        with (
            patch.object(self.processor.buffer, "is_timeout", return_value=True),
            patch.object(self.processor.buffer, "has_content", return_value=True),
        ):
            result = self.processor.check_prompt_candidate(0.02)

            assert result == ("A", True)
            assert self.processor.buffer.get_content() == ""

    def test_check_prompt_candidate_not_candidate(self):
        """Test prompt candidate check when not a candidate"""
        self.processor.buffer.add_data("test")
        self.mock_detector.is_prompt_candidate.return_value = False

        with patch.object(self.processor.buffer, "has_content", return_value=True):
            result = self.processor.check_prompt_candidate(0.02)
            assert result is None

    def test_split_prompt_data_with_prompt(self):
        """Test splitting data with prompt"""
        self.processor.buffer.add_data("line1\nline2\nA>")
        self.mock_detector.detect_prompt.side_effect = lambda x: x == "A>"

        result = self.processor._split_prompt_data()

        expected = [("line1", False), ("line2", False), ("A>", True)]
        assert result == expected

    def test_split_prompt_data_no_prompt(self):
        """Test splitting data without prompt"""
        self.processor.buffer.add_data("line1\nline2\ntext")
        self.mock_detector.detect_prompt.return_value = False

        result = self.processor._split_prompt_data()

        expected = [("line1", False), ("line2", False), ("text", False)]
        assert result == expected

    def test_split_prompt_data_empty_lines(self):
        """Test splitting data with empty lines"""
        self.processor.buffer.add_data("line1\n\nA>")
        self.mock_detector.detect_prompt.side_effect = lambda x: x == "A>"

        result = self.processor._split_prompt_data()

        expected = [("line1", False), ("A>", True)]
        assert result == expected

    def test_has_incomplete_data_true(self):
        """Test incomplete data detection - true case"""
        self.processor.buffer.add_data("incomplete")

        result = self.processor.has_incomplete_data()
        assert result is True

    def test_has_incomplete_data_false_with_newline(self):
        """Test incomplete data detection - false with newline"""
        self.processor.buffer.add_data("complete\n")

        result = self.processor.has_incomplete_data()
        assert result is False

    def test_has_incomplete_data_false_empty(self):
        """Test incomplete data detection - false when empty"""
        result = self.processor.has_incomplete_data()
        assert result is False
