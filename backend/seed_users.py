"""
One-time script to create test users in the database.
Run: python seed_users.py
"""
from database import SessionLocal, init_db
from models import User, Config
from auth import hash_password

def seed_users():
    init_db()
    db = SessionLocal()

    test_users = [
        {"email": "user1@test.com", "password": "password1"},
        {"email": "user2@test.com", "password": "password2"},
        {"email": "user3@test.com", "password": "password3"},
    ]

    for user_data in test_users:
        existing = db.query(User).filter(User.email == user_data["email"]).first()
        if not existing:
            user = User(
                email=user_data["email"],
                password_hash=hash_password(user_data["password"])
            )
            db.add(user)
            db.flush()  # Get the user ID

            # Create default config for the user
            config = Config(
                user_id=user.id,
                stock_universe="NIFTY_50",
                duration_days=120
            )
            db.add(config)
            print(f"Created user: {user_data['email']}")
        else:
            print(f"User already exists: {user_data['email']}")

    db.commit()
    db.close()
    print("User seeding complete!")

if __name__ == "__main__":
    seed_users()
