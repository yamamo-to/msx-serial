from importlib import resources
from jinja2 import Environment, FunctionLoader


def load_template(name):
    try:
        tpl = resources.files('msx_serial.transfer').joinpath(name)
        return tpl.read_text(encoding='utf-8')
    except FileNotFoundError:
        return None


def send_basic_program(program: str, variables: dict) -> str:
    env = Environment(loader=FunctionLoader(load_template))
    template = env.get_template(program)
    rendered = template.render(variables)

    # 各行の末尾の空白を削除し、指定の改行コードで結合
    lines = (line.rstrip() for line in rendered.splitlines())
    new_line = b"\x0d\x0a\x0a".decode("utf-8")
    output = new_line.join(lines) + new_line
    return output
