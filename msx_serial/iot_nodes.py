import yaml
from pathlib import Path


class IotNodes:
    def __init__(self):
        self.nodes = []
        self.load_nodes_from_yaml()

    def load_nodes_from_yaml(self):
        yaml_path = Path(__file__).parent / 'iot_basic_nodes.yml'
        if yaml_path.exists():
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if data and 'nodes' in data:
                    self.nodes = [node['name'] for node in data['nodes']]

    def get_node_names(self):
        return self.nodes

    def complete_node_name(self, text):
        if not text:
            return self.nodes
        return [node for node in self.nodes if node.startswith(text)]


# 使用例
if __name__ == '__main__':
    iot_nodes = IotNodes()
    print("利用可能なノード名:")
    for node in iot_nodes.get_node_names():
        print(f"- {node}")

    # 補完のテスト
    test_input = "host/battery"
    print(f"\n'{test_input}'で始まるノード名:")
    for node in iot_nodes.complete_node_name(test_input):
        print(f"- {node}")
