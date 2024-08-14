from dataclasses import dataclass


@dataclass
class ActiveChannel:
    id: int
    helper_label: str


@dataclass
class ChannelsSetup:
    id: int
    minVolt: float
    maxVolt: float
    load: float


@dataclass
class Step:
    type: int
    description: str
    duration: float
    input_source: int
    channels_setup: list[ChannelsSetup]

    def __post_init__(self):
        channel_setup_list = []
        for channel in self.channels_setup:
            channel_setup_list.append(ChannelsSetup(**channel))
        self.channels_setup = channel_setup_list


@dataclass
class Test:
    group: str
    model: str
    customer: str
    active_channels: list[ActiveChannel]
    input_type: str
    inputs: list[str]
    steps: list[Step]

    def __post_init__(self):
        step_list = []
        active_channels_list = []
        for step in self.steps:
            step_list.append(Step(**step))
        self.steps = step_list
        for channel in self.active_channels:
            active_channels_list.append(ActiveChannel(**channel))
        self.active_channels = active_channels_list