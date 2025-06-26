"""
Tests for protocol module
"""

from unittest.mock import patch

from msx_serial.protocol.msx_detector import MSXMode, MSXProtocolDetector


class TestMSXProtocolDetector:
    """Test MSXProtocolDetector class"""

    def setup_method(self):
        """Setup test"""
        self.detector = MSXProtocolDetector()

    def test_init(self):
        """Test initialization"""
        assert self.detector.current_mode == MSXMode.UNKNOWN.value
        assert self.detector.prompt_pattern is not None
        assert self.detector.basic_prompt_pattern is not None
        assert self.detector.dos_prompt_pattern is not None

    # Test prompt detection
    def test_detect_prompt_basic(self):
        """Test detection of BASIC prompts"""
        assert self.detector.detect_prompt("Ok")
        assert self.detector.detect_prompt("ok")
        assert self.detector.detect_prompt("OK")
        assert self.detector.detect_prompt("Ok ")

    def test_detect_prompt_dos(self):
        """Test detection of DOS prompts"""
        assert self.detector.detect_prompt("A:>")
        assert self.detector.detect_prompt("B:>")
        assert self.detector.detect_prompt("C:> ")

    def test_detect_prompt_general(self):
        """Test detection of general prompts"""
        assert self.detector.detect_prompt("A>")
        assert self.detector.detect_prompt("B>")
        assert self.detector.detect_prompt("Z> ")

    def test_detect_prompt_false(self):
        """Test non-prompts are not detected"""
        assert not self.detector.detect_prompt("Hello")
        assert not self.detector.detect_prompt("A:")
        assert not self.detector.detect_prompt("O")
        assert not self.detector.detect_prompt("test A>")
        assert not self.detector.detect_prompt("")

    # Test prompt candidate detection
    def test_is_prompt_candidate_single_letter(self):
        """Test single letter prompt candidates"""
        assert self.detector.is_prompt_candidate("A")
        assert self.detector.is_prompt_candidate("B")
        assert self.detector.is_prompt_candidate("Z")

    def test_is_prompt_candidate_dos_partial(self):
        """Test DOS prompt candidates"""
        assert self.detector.is_prompt_candidate("A:")
        assert self.detector.is_prompt_candidate("B:")
        assert self.detector.is_prompt_candidate("C:")

    def test_is_prompt_candidate_basic_partial(self):
        """Test BASIC prompt candidates"""
        assert self.detector.is_prompt_candidate("O")
        assert self.detector.is_prompt_candidate("o")
        assert self.detector.is_prompt_candidate("Ok")
        assert self.detector.is_prompt_candidate("ok")

    def test_is_prompt_candidate_false(self):
        """Test non-candidates are not detected"""
        assert not self.detector.is_prompt_candidate("Hello")
        assert not self.detector.is_prompt_candidate("AB")
        assert not self.detector.is_prompt_candidate("123")
        assert not self.detector.is_prompt_candidate("")
        assert not self.detector.is_prompt_candidate("a")  # lowercase

    # Test mode detection
    def test_detect_mode_basic(self):
        """Test BASIC mode detection"""
        assert self.detector.detect_mode("Ok") == MSXMode.BASIC
        assert self.detector.detect_mode("ok") == MSXMode.BASIC
        assert self.detector.detect_mode("OK") == MSXMode.BASIC

    def test_detect_mode_dos_colon(self):
        """Test DOS mode detection with colon"""
        assert self.detector.detect_mode("A:>") == MSXMode.DOS
        assert self.detector.detect_mode("B:>") == MSXMode.DOS
        assert self.detector.detect_mode("C:>") == MSXMode.DOS

    def test_detect_mode_dos_general(self):
        """Test DOS mode detection for general prompts"""
        assert self.detector.detect_mode("A>") == MSXMode.DOS
        assert self.detector.detect_mode("B>") == MSXMode.DOS
        assert self.detector.detect_mode("Z>") == MSXMode.DOS

    def test_detect_mode_unknown(self):
        """Test unknown mode detection"""
        assert self.detector.detect_mode("Hello") == MSXMode.UNKNOWN
        assert self.detector.detect_mode("") == MSXMode.UNKNOWN
        assert self.detector.detect_mode("test") == MSXMode.UNKNOWN

    # Test mode update
    def test_update_mode_change(self):
        """Test mode update when mode changes"""
        initial_mode = self.detector.current_mode
        result = self.detector.update_mode(MSXMode.BASIC)

        assert result is True
        assert self.detector.current_mode == MSXMode.BASIC.value
        assert self.detector.current_mode != initial_mode

    def test_update_mode_no_change(self):
        """Test mode update when mode doesn't change"""
        self.detector.current_mode = MSXMode.BASIC.value
        result = self.detector.update_mode(MSXMode.BASIC)

        assert result is False
        assert self.detector.current_mode == MSXMode.BASIC.value

    # Test force mode update
    def test_force_mode_update_basic(self):
        """Test force mode update with BASIC prompt"""
        result = self.detector.force_mode_update("Ok")

        assert result is True
        assert self.detector.current_mode == MSXMode.BASIC.value

    def test_force_mode_update_dos(self):
        """Test force mode update with DOS prompt"""
        result = self.detector.force_mode_update("A:>")

        assert result is True
        assert self.detector.current_mode == MSXMode.DOS.value

    def test_force_mode_update_unknown(self):
        """Test force mode update with unknown prompt"""
        original_mode = self.detector.current_mode
        result = self.detector.force_mode_update("invalid")

        assert result is False
        assert self.detector.current_mode == original_mode

    def test_force_mode_update_general_prompt(self):
        """Test force mode update with general prompt (should be DOS)"""
        result = self.detector.force_mode_update("A>")

        assert result is True
        assert self.detector.current_mode == MSXMode.DOS.value


def test_debug_print_enabled(capsys):
    detector = MSXProtocolDetector(debug_mode=True)
    with patch("msx_serial.protocol.msx_detector.print_info") as mock_print:
        detector._debug_print("test debug")
        mock_print.assert_called_once()


def test_debug_print_disabled():
    detector = MSXProtocolDetector(debug_mode=False)
    with patch("msx_serial.protocol.msx_detector.print_info") as mock_print:
        detector._debug_print("should not print")
        mock_print.assert_not_called()


def test_enable_disable_debug():
    detector = MSXProtocolDetector(debug_mode=False)
    with patch("msx_serial.protocol.msx_detector.print_info") as mock_print:
        detector.enable_debug()
        assert detector.debug_mode is True
        mock_print.assert_called_once_with("MSX protocol detection debug mode enabled")
    with patch("msx_serial.protocol.msx_detector.print_info") as mock_print:
        detector.disable_debug()
        assert detector.debug_mode is False
        mock_print.assert_called_once_with("MSX protocol detection debug mode disabled")


def test_detect_prompt_multiline_basic():
    detector = MSXProtocolDetector()
    multi = "Hello\nOk"
    assert detector.detect_prompt(multi) is True


def test_detect_prompt_multiline_dos():
    detector = MSXProtocolDetector()
    multi = "Hello\nA:>"
    assert detector.detect_prompt(multi) is True


def test_detect_prompt_multiline_false():
    detector = MSXProtocolDetector()
    multi = "Hello\nWorld"
    assert detector.detect_prompt(multi) is False


def test_detect_mode_multiline_unknown():
    detector = MSXProtocolDetector()
    multi = "Hello\nWorld"
    assert detector.detect_mode(multi).value == "unknown"


def test_detect_mode_multiline_unknown_debug():
    detector = MSXProtocolDetector(debug_mode=True)
    multi = "Hello\nWorld"
    with patch("msx_serial.protocol.msx_detector.print_info") as mock_print:
        mode = detector.detect_mode(multi)
        assert mode.value == "unknown"
        mock_print.assert_any_call("[MSX Debug] Unknown mode from multi-line prompt")


def test_detect_mode_singleline_unknown_debug():
    detector = MSXProtocolDetector(debug_mode=True)
    with patch("msx_serial.protocol.msx_detector.print_info") as mock_print:
        mode = detector.detect_mode("???")
        assert mode.value == "unknown"
        # else節のdebug出力
        mock_print.assert_any_call("[MSX Debug] Unknown mode from prompt: '???'")
