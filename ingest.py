import os
from database import SessionLocal
from models import Patient

DATA_DIR = "data"

def seed_database():
    db = SessionLocal()

    try:
        for file in os.listdir(DATA_DIR):

            if file.endswith(".json"):

                # Extract MRD from filename
                mrd_number = file.replace(".json", "")

                # Check if already exists
                existing = db.query(Patient).filter_by(mrd_number=mrd_number).first()

                if not existing:
                    patient = Patient(
                        mrd_number=mrd_number,
                        file_path=os.path.join(DATA_DIR, file)
                    )
                    db.add(patient)
                    print(f"Inserted: {mrd_number}")

        db.commit()

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

print("✅ Data Ingested")