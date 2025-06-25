"""
Performance control commands for MSX Terminal
"""

from ..common.color_output import print_info, print_error


def handle_performance_command(terminal: object, command: str) -> bool:
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
    elif subcommand == "debug":
        if len(cmd_parts) >= 3:
            mode = cmd_parts[2].lower()
            if mode in ["on", "off", "toggle"]:
                _handle_debug_mode(terminal, mode)
            else:
                print_error("Invalid debug mode. Use: on, off, or toggle")
        else:
            _handle_debug_mode(terminal, "toggle")
    elif subcommand == "help":
        _show_performance_help()
    else:
        print_error(f"Unknown performance command: {subcommand}")
        _show_performance_help()

    return True


def _show_performance_stats(terminal: object) -> None:
    """Show performance statistics"""
    print_info("=== Performance Statistics ===")
    print_info("Mode: Optimized (instant processing)")
    print_info("Receive Delay: 0.0001s")
    print_info("Batch Size: 1 byte (character-by-character)")
    print_info(f"Encoding: {getattr(terminal, 'encoding', 'Unknown')}")

    # Debug mode status
    debug_mode = getattr(
        getattr(terminal, "protocol_detector", None), "debug_mode", False
    )
    print_info(f"Debug Mode: {'Yes' if debug_mode else 'No'}")


def _handle_debug_mode(terminal: object, mode: str) -> None:
    """Handle debug mode commands

    Args:
        terminal: Terminal instance
        mode: "on", "off", or "toggle"
    """
    if not hasattr(terminal, "toggle_debug_mode"):
        print_error("Debug mode not available in this terminal version")
        return

    current_debug = getattr(
        getattr(terminal, "protocol_detector", None), "debug_mode", False
    )

    if mode == "on":
        if not current_debug:
            terminal.toggle_debug_mode()
        else:
            print_info("Debug mode is already enabled")
    elif mode == "off":
        if current_debug:
            terminal.toggle_debug_mode()
        else:
            print_info("Debug mode is already disabled")
    elif mode == "toggle":
        terminal.toggle_debug_mode()


def _show_performance_help() -> None:
    """Show performance help"""
    print_info("Performance Commands:")
    print_info("  @perf stats         - Show performance statistics")
    print_info("  @perf debug [on|off|toggle] - Control debug mode")
    print_info("  @perf help          - Show this help")
    print_info("")
    print_info("Note: Terminal is optimized for instant character processing")
    print_info("Debug mode shows detailed protocol detection information")
