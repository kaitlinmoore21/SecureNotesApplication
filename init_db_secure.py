from app.secure.database import engine
from app.secure.models import Base

print("Creating secure DB...")
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
print("Done.")
