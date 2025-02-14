import sys
from naledi import create_app
import os

# temporary fix for the issue with the dotenv package
from dotenv import load_dotenv

print("✅ Loading .env file...")

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
print("loading .env from ", {dotenv_path})
# Manually load .env file

if not os.path.exists(dotenv_path):
    print("❌ error: .env file not found")
    exit(1)




load_dotenv(dotenv_path=dotenv_path, verbose=True)


db_uri = os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL")
try:
    print("trying to create flask app")
    app = create_app()  # Explicitly call the function
    print("✅ Flask Application Created Successfully")
except Exception as e:
    print("❌ ERROR: App creation failed:", e)
    sys.exit(1)  # Exit with error

if __name__ == "__main__":
    try:
        print("✅ Running Flask App on port 5000")
        app.run(debug=True, port=5000)
    except Exception as e:
        print("❌ ERROR: Flask App failed to run:", e)

