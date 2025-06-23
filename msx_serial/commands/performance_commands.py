"""
Performance control commands for MSX Terminal
"""

from ..ui.color_output import print_info, print_error


def handle_performance_command(terminal, command: str) -> bool:
    """Handle performance-related commands

    Args:
        terminal: Terminal instance
        command: Performance command

    Returns:
        True if command was handled
    """
    cmd_parts = command.split()

    if len(cmd_parts) < 2:
        _show_performance_help()
        return True

    subcommand = cmd_parts[1].lower()

    if subcommand == "stats":
        _show_performance_stats(terminal)
    elif subcommand == "toggle":
        _toggle_fast_mode(terminal)
    elif subcommand == "responsive":
        if len(cmd_parts) >= 3:
            mode = cmd_parts[2].lower()
            if mode in ["on", "off", "toggle"]:
                _handle_responsive_mode(terminal, mode)
            else:
                print_error("Invalid responsive mode. Use: on, off, or toggle")
        else:
            _handle_responsive_mode(terminal, "toggle")
    elif subcommand == "instant":
        if len(cmd_parts) >= 3:
            mode = cmd_parts[2].lower()
            if mode in ["on", "off", "toggle"]:
                _handle_instant_mode(terminal, mode)
            else:
                print_error("Invalid instant mode. Use: on, off, or toggle")
        else:
            _handle_instant_mode(terminal, "toggle")
    elif subcommand == "mode":
        if len(cmd_parts) >= 3:
            mode = cmd_parts[2].lower()
            if mode in ["fast", "normal", "responsive", "instant"]:
                _set_performance_mode(terminal, mode)
            else:
                print_error("Invalid mode. Use: fast, normal, responsive, or instant")
        else:
            print_error("Mode required. Use: fast, normal, responsive, or instant")
    elif subcommand == "help":
        _show_performance_help()
    else:
        print_error(f"Unknown performance command: {subcommand}")
        _show_performance_help()

    return True


def _show_performance_stats(terminal):
    """Show performance statistics"""
    if hasattr(terminal, "get_performance_stats"):
        stats = terminal.get_performance_stats()

        print_info("=== Performance Statistics ===")
        print_info(f"Fast Mode: {'Yes' if stats.get('fast_mode', False) else 'No'}")
        print_info(
            f"Responsive Mode: {'Yes' if stats.get('responsive_mode', False) else 'No'}"
        )
        print_info(
            f"Instant Mode: {'Yes' if stats.get('instant_mode', False) else 'No'}"
        )
        print_info(f"Receive Delay: {stats.get('receive_delay', 'Unknown')}s")
        print_info(f"Batch Size: {stats.get('batch_size', 'Unknown')} bytes")
        print_info(f"Encoding: {stats.get('encoding', 'Unknown')}")

        # Display statistics if available
        if "fast_calls" in stats:
            print_info(f"Fast Display Calls: {stats.get('fast_calls', 0)}")
            print_info(f"Full Display Calls: {stats.get('full_calls', 0)}")
            print_info(f"Total Calls: {stats.get('total_calls', 0)}")
            print_info(f"Fast Ratio: {stats.get('fast_ratio', 0):.1f}%")
            print_info(f"Display Mode: {stats.get('display_mode', 'Unknown')}")

        # Performance recommendations
        instant_mode = stats.get("instant_mode", False)
        responsive_mode = stats.get("responsive_mode", False)

        if not instant_mode and not responsive_mode:
            print_info("\n💡 For best DIR command response, try: @perf instant on")
        elif not instant_mode and responsive_mode:
            print_info("\n💡 For ultimate DIR command response, try: @perf instant on")
    else:
        print_error("Performance statistics not available")


def _toggle_fast_mode(terminal):
    """Toggle fast mode"""
    if hasattr(terminal, "toggle_fast_mode"):
        terminal.toggle_fast_mode()
    else:
        print_error("Fast mode toggle not available")


def _handle_responsive_mode(terminal, mode: str):
    """Handle responsive mode commands

    Args:
        terminal: Terminal instance
        mode: "on", "off", or "toggle"
    """
    if not hasattr(terminal, "responsive_mode"):
        print_error("Responsive mode not available in this terminal version")
        return

    if mode == "on":
        if not terminal.responsive_mode:
            if hasattr(terminal, "toggle_responsive_mode"):
                terminal.toggle_responsive_mode()
        else:
            print_info("Responsive mode is already enabled")
    elif mode == "off":
        if terminal.responsive_mode:
            if hasattr(terminal, "toggle_responsive_mode"):
                terminal.toggle_responsive_mode()
        else:
            print_info("Responsive mode is already disabled")
    elif mode == "toggle":
        if hasattr(terminal, "toggle_responsive_mode"):
            terminal.toggle_responsive_mode()
        else:
            print_error("Responsive mode toggle not available")


def _handle_instant_mode(terminal, mode: str):
    """Handle instant mode commands

    Args:
        terminal: Terminal instance
        mode: "on", "off", or "toggle"
    """
    if not hasattr(terminal, "instant_mode"):
        print_error("Instant mode not available in this terminal version")
        return

    if mode == "on":
        if not terminal.instant_mode:
            if hasattr(terminal, "toggle_instant_mode"):
                terminal.toggle_instant_mode()
        else:
            print_info("Instant mode is already enabled")
    elif mode == "off":
        if terminal.instant_mode:
            if hasattr(terminal, "toggle_instant_mode"):
                terminal.toggle_instant_mode()
        else:
            print_info("Instant mode is already disabled")
    elif mode == "toggle":
        if hasattr(terminal, "toggle_instant_mode"):
            terminal.toggle_instant_mode()
        else:
            print_error("Instant mode toggle not available")


def _set_performance_mode(terminal, mode: str):
    """Set performance mode

    Args:
        terminal: Terminal instance
        mode: "fast", "normal", "responsive", or "instant"
    """
    if mode == "instant":
        # Enable fast mode and instant mode, disable responsive mode if separate
        if hasattr(terminal, "fast_mode") and not terminal.fast_mode:
            if hasattr(terminal, "toggle_fast_mode"):
                terminal.toggle_fast_mode()

        if hasattr(terminal, "instant_mode") and not terminal.instant_mode:
            if hasattr(terminal, "toggle_instant_mode"):
                terminal.toggle_instant_mode()

        print_info("Performance mode set to: Instant (zero-buffering for DIR commands)")

    elif mode == "responsive":
        # Enable both fast mode and responsive mode, disable instant mode
        if hasattr(terminal, "fast_mode") and not terminal.fast_mode:
            if hasattr(terminal, "toggle_fast_mode"):
                terminal.toggle_fast_mode()

        if hasattr(terminal, "instant_mode") and terminal.instant_mode:
            if hasattr(terminal, "toggle_instant_mode"):
                terminal.toggle_instant_mode()

        if hasattr(terminal, "responsive_mode") and not terminal.responsive_mode:
            if hasattr(terminal, "toggle_responsive_mode"):
                terminal.toggle_responsive_mode()

        print_info("Performance mode set to: Responsive (optimized for DIR commands)")

    elif mode == "fast":
        # Enable fast mode, disable responsive and instant modes
        if hasattr(terminal, "fast_mode") and not terminal.fast_mode:
            if hasattr(terminal, "toggle_fast_mode"):
                terminal.toggle_fast_mode()

        if hasattr(terminal, "instant_mode") and terminal.instant_mode:
            if hasattr(terminal, "toggle_instant_mode"):
                terminal.toggle_instant_mode()

        if hasattr(terminal, "responsive_mode") and terminal.responsive_mode:
            if hasattr(terminal, "toggle_responsive_mode"):
                terminal.toggle_responsive_mode()

        print_info("Performance mode set to: Fast")

    elif mode == "normal":
        # Disable all optimization modes
        if hasattr(terminal, "instant_mode") and terminal.instant_mode:
            if hasattr(terminal, "toggle_instant_mode"):
                terminal.toggle_instant_mode()

        if hasattr(terminal, "responsive_mode") and terminal.responsive_mode:
            if hasattr(terminal, "toggle_responsive_mode"):
                terminal.toggle_responsive_mode()

        if hasattr(terminal, "fast_mode") and terminal.fast_mode:
            if hasattr(terminal, "toggle_fast_mode"):
                terminal.toggle_fast_mode()

        print_info("Performance mode set to: Normal")


def _show_performance_help():
    """Show performance command help"""
    help_text = """
=== Performance Commands ===

@perf stats                      - Show performance statistics
@perf toggle                     - Toggle fast mode on/off
@perf responsive [on|off|toggle] - Control responsive mode
@perf instant [on|off|toggle]    - Control instant mode (best for DIR commands)
@perf mode [fast|normal|responsive|instant] - Set overall performance mode
@perf help                       - Show this help

Performance Modes:
• instant    - Character-by-character instant display (best for DIR, FILES) ⭐
• responsive - Maximum responsiveness with minimal buffering
• fast       - Good performance balance
• normal     - Standard operation

Features:
• Instant mode eliminates "batched display" issues completely
• Characters appear immediately as received from MSX
• Perfect for real-time commands like DIR, FILES, TYPE
• Smart newline handling prevents character-per-line display
• Zero buffering delay for true real-time experience

Quick Setup:
@perf instant on    - Enable instant character-by-character display
@perf mode instant  - Full instant mode setup
"""
    print_info(help_text)
