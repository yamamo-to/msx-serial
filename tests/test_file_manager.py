"""
Tests for file manager module
"""

import base64
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from msx_serial.transfer.file_manager import (
    FileReader,
    DataEncoder,
    TransferSession,
    FileUploader,
    ProgressTracker,
)


class TestFileReader:
    """Test FileReader class"""

    @patch("builtins.open", mock_open(read_data=b"test content"))
    @patch("chardet.detect")
    def test_detect_encoding(self, mock_detect):
        """Test encoding detection"""
        mock_detect.return_value = {"encoding": "utf-8"}

        result = FileReader.detect_encoding(Path("test.txt"))

        assert result == "utf-8"
        mock_detect.assert_called_once_with(b"test content")

    @patch("builtins.open", mock_open(read_data=b"test content"))
    @patch("chardet.detect")
    def test_detect_encoding_none(self, mock_detect):
        """Test encoding detection when chardet returns None"""
        mock_detect.return_value = {"encoding": None}

        result = FileReader.detect_encoding(Path("test.txt"))

        assert result == "utf-8"

    @patch("builtins.open", mock_open(read_data="line1\nline2\nline3"))
    def test_read_text_file_with_encoding(self):
        """Test reading text file with specified encoding"""
        lines = list(FileReader.read_text_file(Path("test.txt"), "utf-8"))

        assert lines == ["line1", "line2", "line3"]

    @patch("builtins.open", mock_open(read_data="line1\nline2\nline3"))
    @patch.object(FileReader, "detect_encoding")
    def test_read_text_file_auto_detect(self, mock_detect):
        """Test reading text file with auto-detected encoding"""
        mock_detect.return_value = "shift_jis"

        lines = list(FileReader.read_text_file(Path("test.txt")))

        assert lines == ["line1", "line2", "line3"]
        mock_detect.assert_called_once_with(Path("test.txt"))

    @patch("builtins.open", mock_open(read_data=b"binary content"))
    def test_read_binary_file(self):
        """Test reading binary file"""
        result = FileReader.read_binary_file(Path("test.bin"))

        assert result == b"binary content"


class TestDataEncoder:
    """Test DataEncoder class"""

    def test_encode_base64(self):
        """Test base64 encoding"""
        data = b"hello world"
        result = DataEncoder.encode_base64(data)

        expected = base64.b64encode(data).decode("ascii")
        assert result == expected

    def test_chunk_data_default_size(self):
        """Test chunking data with default size"""
        data = "a" * 100
        chunks = list(DataEncoder.chunk_data(data))

        assert len(chunks) == 2
        assert chunks[0] == "a" * 76
        assert chunks[1] == "a" * 24

    def test_chunk_data_custom_size(self):
        """Test chunking data with custom size"""
        data = "hello world"
        chunks = list(DataEncoder.chunk_data(data, 5))

        assert chunks == ["hello", " worl", "d"]

    def test_chunk_data_exact_size(self):
        """Test chunking data with exact size"""
        data = "hello"
        chunks = list(DataEncoder.chunk_data(data, 5))

        assert chunks == ["hello"]


class TestTransferSession:
    """Test TransferSession class"""

    def setup_method(self):
        """Setup test"""
        self.mock_connection = Mock()
        self.session = TransferSession(self.mock_connection, "utf-8")

    def test_init(self):
        """Test initialization"""
        assert self.session.connection == self.mock_connection
        assert self.session.encoding == "utf-8"
        assert self.session._suppress_callback is None

    def test_set_output_suppression_callback(self):
        """Test setting output suppression callback"""
        callback = Mock()
        self.session.set_output_suppression_callback(callback)

        assert self.session._suppress_callback == callback

    def test_suppress_output_with_callback(self):
        """Test suppressing output with callback"""
        callback = Mock()
        self.session.set_output_suppression_callback(callback)

        self.session.suppress_output(True)

        callback.assert_called_once_with(True)

    def test_suppress_output_without_callback(self):
        """Test suppressing output without callback"""
        self.session.suppress_output(True)
        # Should not raise any exception

    def test_send_data(self):
        """Test sending data"""
        self.session.send_data("test data")

        self.mock_connection.write.assert_called_once_with(b"test data")
        self.mock_connection.flush.assert_called_once()

    def test_send_bytes(self):
        """Test sending bytes"""
        self.session.send_bytes(b"test bytes")

        self.mock_connection.write.assert_called_once_with(b"test bytes")
        self.mock_connection.flush.assert_called_once()


class TestFileUploader:
    """Test FileUploader class"""

    def setup_method(self):
        """Setup test"""
        self.mock_session = Mock(spec=TransferSession)
        self.uploader = FileUploader(self.mock_session)

    def test_init(self):
        """Test initialization"""
        assert self.uploader.session == self.mock_session
        assert self.uploader.chunk_size == 76

    @patch.object(FileReader, "read_binary_file")
    @patch.object(DataEncoder, "encode_base64")
    @patch.object(DataEncoder, "chunk_data")
    def test_upload_as_base64_success(self, mock_chunk, mock_encode, mock_read):
        """Test successful base64 upload"""
        mock_read.return_value = b"file content"
        mock_encode.return_value = "encoded_data"
        mock_chunk.return_value = ["chunk1", "chunk2"]

        progress_callback = Mock()
        result = self.uploader.upload_as_base64(Path("test.txt"), progress_callback)

        assert result is True
        mock_read.assert_called_once_with(Path("test.txt"))
        mock_encode.assert_called_once_with(b"file content")
        mock_chunk.assert_called_once_with("encoded_data", 76)

        # Check data sending
        expected_calls = ["chunk1\r\n", "chunk2\r\n", "`\r\n"]
        actual_calls = [
            call[0][0] for call in self.mock_session.send_data.call_args_list
        ]
        assert actual_calls == expected_calls

        # Check progress callbacks
        assert progress_callback.call_count == 2

    @patch.object(FileReader, "read_binary_file")
    def test_upload_as_base64_failure(self, mock_read):
        """Test failed base64 upload"""
        mock_read.side_effect = Exception("File error")

        result = self.uploader.upload_as_base64(Path("test.txt"))

        assert result is False

    @patch.object(FileReader, "read_text_file")
    def test_paste_text_file_success(self, mock_read):
        """Test successful text file paste"""
        mock_read.return_value = ["line1", "line2", "line3"]

        result = self.uploader.paste_text_file(Path("test.txt"), "utf-8")

        assert result is True
        mock_read.assert_called_once_with(Path("test.txt"))

        # Check that each line was encoded and sent
        expected_calls = [b"line1", b"line2", b"line3"]
        actual_calls = [
            call[0][0] for call in self.mock_session.send_bytes.call_args_list
        ]
        assert actual_calls == expected_calls

    @patch.object(FileReader, "read_text_file")
    def test_paste_text_file_failure(self, mock_read):
        """Test failed text file paste"""
        mock_read.side_effect = Exception("Read error")

        result = self.uploader.paste_text_file(Path("test.txt"), "utf-8")

        assert result is False


class TestProgressTracker:
    """Test ProgressTracker class"""

    @patch("msx_serial.transfer.file_manager.print_info")
    def test_init(self, mock_print):
        """Test initialization"""
        tracker = ProgressTracker(100, "Test Progress")

        assert tracker.total == 100
        assert tracker.current == 0
        assert tracker.description == "Test Progress"

    @patch("msx_serial.transfer.file_manager.print_info")
    def test_update_progress(self, mock_print):
        """Test updating progress"""
        tracker = ProgressTracker(100, "Test")

        tracker.update(25)

        assert tracker.current == 25
        mock_print.assert_called_with("Test: 25.0% (25/100)")

    @patch("msx_serial.transfer.file_manager.print_info")
    def test_update_progress_zero_total(self, mock_print):
        """Test updating progress with zero total"""
        tracker = ProgressTracker(0, "Test")

        tracker.update(10)

        assert tracker.current == 10
        mock_print.assert_called_with("Test: 0.0% (10/0)")

    @patch("msx_serial.transfer.file_manager.print_info")
    def test_finish(self, mock_print):
        """Test finishing progress"""
        tracker = ProgressTracker(100, "Test")

        tracker.finish()

        mock_print.assert_called_with("Test: Complete")
