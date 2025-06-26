"""
Basic program template processor
"""

from importlib import resources
from typing import Optional

from jinja2 import Environment, FunctionLoader


def load_template(name: str) -> Optional[str]:
    """Load template from package resources

    Args:
        name: Template name

    Returns:
        Template content or None if not found
    """
    try:
        tpl = resources.files("msx_serial.transfer").joinpath(name)
        return tpl.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None


def send_basic_program(program: str, variables: dict[str, str]) -> str:
    """Generate BASIC program from template

    Args:
        program: Template name
        variables: Template variables

    Returns:
        Generated BASIC program with proper line endings
    """
    env = Environment(
        loader=FunctionLoader(load_template),
        autoescape=True,  # セキュリティ向上のためautoescapeを有効化
    )
    template = env.get_template(program)
    rendered = template.render(variables)

    # 各行の末尾の空白を削除し、指定の改行コードで結合
    lines = (line.rstrip() for line in rendered.splitlines())
    new_line = "\r\n"
    output = new_line.join(lines) + new_line
    return output
