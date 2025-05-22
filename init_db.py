# init_db.py
from app.database import engine
from app import models

models.Base.metadata.create_all(bind=engine)
print("✅ Tables created.")
