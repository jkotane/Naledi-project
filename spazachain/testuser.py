from spazachain.models import db, UserProfile
from werkzeug.security import generate_password_hash

new_user = UserProfile(
    username="testuser",
    email="testuser@example.com",
    cellno="0821234567",
    user_password=generate_password_hash("SecurePassword123", method='pbkdf2:sha256')
)

try:
    db.session.add(new_user)
    db.session.commit()
    print("Test user added successfully.")
except Exception as e:
    db.session.rollback()
    print(f"Error adding test user: {e}")
