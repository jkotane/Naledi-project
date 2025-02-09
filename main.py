import sys
from naledi import create_app
import os

# Debugging Print
print("✅ Starting Flask Application...")


try:
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

