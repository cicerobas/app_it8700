from enum import Enum


class TestState(Enum):
    RUNNING = "Testando"
    PAUSED = "Pausado"
    CANCELED = "Cancelado"
    PASSED = "Aprovado"
    FAILED = "Reprovado"
    NONE = ""