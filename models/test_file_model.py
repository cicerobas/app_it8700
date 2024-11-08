from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class LoadParameter:
    id: int
    tag: str
    voltage_under_limit: Optional[float] = None
    voltage_upper: Optional[float] = None
    voltage_lower: Optional[float] = None
    static_load: Optional[float] = None
    end_load: Optional[float] = None
    load_upper: Optional[float] = None
    load_lower: Optional[float] = None
    increase_step: Optional[float] = None
    increase_delay: Optional[float] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LoadParameter':
        return cls(
            id=data['id'],
            tag=data['tag'],
            voltage_under_limit=data.get('voltage_under_limit'),
            voltage_upper=data.get('voltage_upper'),
            voltage_lower=data.get('voltage_lower'),
            static_load=data.get('static_load'),
            end_load=data.get('end_load'),
            load_upper=data.get('load_upper'),
            load_lower=data.get('load_lower'),
            increase_step=data.get('increase_step'),
            increase_delay=data.get('increase_delay')
        )


@dataclass
class ChannelConfiguration:
    channel_id: int
    parameters_id: int


@dataclass
class Step:
    step_type: int
    description: str
    duration: float
    input_source: int
    channels_configuration: Dict[int, LoadParameter]

@dataclass
class ActiveChannel:
    id: int
    label: str


@dataclass
class TestData:
    group: str
    model: str
    customer: str
    input_type: str
    input_sources: List[int]
    active_channels: List[ActiveChannel] = field(default_factory=list)
    load_parameters: List[LoadParameter] = field(default_factory=list)
    steps: List[Step] = field(default_factory=list)
    notes: str = ""

    def __post_init__(self):
        self.active_channels = [ActiveChannel(**item) for item in self.active_channels]
        self.load_parameters = [LoadParameter(**item) for item in self.load_parameters]
        parameters_mapping = {param.id: param for param in self.load_parameters}

        self.steps = [
            Step(
                step_type=item["step_type"],
                description=item["description"],
                duration=item["duration"],
                input_source=item["input_source"],
                channels_configuration={
                    config["channel_id"]: parameters_mapping[config["parameters_id"]]
                    for config in item["channels_configuration"]
                },
            )
            for item in self.steps
        ]
