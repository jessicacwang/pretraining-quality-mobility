from typing import Dict, List 

class SankeyBuilder:
    def __init__(self):
        self.labels: List[str] = []
        self.customdata: List[str] = [] # raw value per node 
        self._index: Dict[str, int] = {}

        self.link_source: List[int] = []
        self.link_target: List[int] = []
        self.link_value: List[float] = []
        self.link_label: List[str] = []

    def node(self, key: str, label: str, value: str) -> int:
        """Register a node under an internal key so that re-registering the same key has no effect"""
        if key not in self._index:
            self._index[key] = len(self.labels)
            self.labels.append(label)
            self.customdata.append(value)
        return self._index[key]

    def link(self, source_key: str, target_key: str, value: float, label: str = ""):
        if value <= 0:
            return 

        self.link_source.append(self._index[source_key])
        self.link_target.append(self._index[target_key])
        self.link_value.append(value)
        self.link_label.append(label)

    def to_dict(self) -> Dict:
        return {
            "node": {
                "label": self.labels,
                "customdata": self.customdata,
                "pad": 15,
                "thickness": 18,
            },
            "link": {
                "source": self.link_source,
                "target": self.link_target,
                "value": self.link_value,
                "label": self.link_label
            }
        }