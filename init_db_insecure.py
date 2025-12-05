from app.insecure.database import engine
from app.insecure.models import Base

print("Creating insecure DB...")
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
print("Done.")
