from app.infrastructure.database import engine
from app.domain.models.base import Base

# import all models so they register with Base.metadata
import app.domain.models.organization  # noqa
import app.domain.models.user  # noqa
import app.domain.models.framework  # noqa
import app.domain.models.control  # noqa
import app.domain.models.evidence  # noqa
import app.domain.models.task  # noqa
import app.domain.models.ai_pipeline  # noqa
import app.domain.models.classifier_output  # noqa

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")