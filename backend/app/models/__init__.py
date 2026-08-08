"""Package marker — imports all models so SQLAlchemy metadata is populated."""
from app.models.user import User
from app.models.project import Project

__all__ = ["User", "Project"]
