from __future__ import annotations

from typing import TYPE_CHECKING, TypeAlias

if TYPE_CHECKING:
    from .models import OpengaussIntegration
    from .vector_stores import OpenGaussDatabase

    ActorInputsDb: TypeAlias = OpengaussIntegration
    VectorDb: TypeAlias = OpenGaussDatabase
