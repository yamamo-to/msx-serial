import importlib
import yaml


class IotNodes:
    def __init__(self) -> None:
        self.nodes: list[str] = []
        self.load_nodes_from_yaml()

    def load_nodes_from_yaml(self) -> None:
        with (
            importlib.resources.files("msx_serial.data")
            .joinpath("iot_basic_nodes.yml")
            .open("r", encoding="utf-8") as f
        ):
            data = yaml.safe_load(f)
            if data and "nodes" in data:
                self.nodes = [node["name"] for node in data["nodes"]]

    def get_node_names(self) -> list[str]:
        return self.nodes

    def complete_node_name(self, text: str) -> list[str]:
        if not text:
            return self.nodes
        return [node for node in self.nodes if node.startswith(text)]
