"""EVLOP v4.0: Universal Self-Evolving Agent Framework, HomeRail DAG Engine & Whole-System Mount SDK."""

from evlop.models import Episode, EvlopConfig, FailureDiagnosis, Gene, VerifyRecord
from evlop.sdk import EvlopEngine

__version__ = "0.4.0"

__all__ = [
    "__version__",
    "EvlopEngine",
    "EvlopConfig",
    "VerifyRecord",
    "FailureDiagnosis",
    "Episode",
    "Gene",
]
