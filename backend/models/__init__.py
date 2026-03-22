# Import all models here to register them with Base.metadata
from .user import User
from .file import File
from .chapter import Chapter
from .reading_history import ReadingHistory


MODEL_REGISTRY = {
    'user': User,
    'file': File,
    'chapter': Chapter,
    'reading_history': ReadingHistory,
}


__all__ = [
    "User",
    "File",
    "Chapter",
    "ReadingHistory",
    "MODEL_REGISTRY",
]


def get_all_models():
    return list(MODEL_REGISTRY.values())


def get_model_by_name(name: str):
    return MODEL_REGISTRY.get(name.lower())
