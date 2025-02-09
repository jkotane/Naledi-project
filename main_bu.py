import sys
from naledi import create_app
#from naledi import naledi

# ✅ Debugging Print
print("✅ Starting Flask Application...")

try:
    app = create_app()  # Explicitly call the function
    print("✅ Flask Application Created Successfully")
except Exception as e:
    print("❌ ERROR: App creation failed:", e)
    sys.exit(1)  # Exit with error

# ✅ Register Blueprints (Ensures Both Apps are Accessible)
from spazachain.spachainauth import spachainauth
from spazachain.spachainview import spachainview
from mncchain.mncauth import mncauth
from mncchain.mncview import mncview

"""app.register_blueprint(spachainauth, url_prefix='/spazachain/auth')
app.register_blueprint(spachainview, url_prefix='/spazachain/view')
app.register_blueprint(mncauth, url_prefix='/mncchain/auth')
app.register_blueprint(mncview, url_prefix='/mncchain/view') """



#app.register_blueprint(naledi)


app.register_blueprint(spachainauth, url_prefix='/spazachain/home')
app.register_blueprint(spachainview, url_prefix='/spazachain/view')
app.register_blueprint(mncauth, url_prefix='/mncchain/home')
app.register_blueprint(mncview, url_prefix='/mncchain/view')

if __name__ == "__main__":
    try:
        print("✅ Running Flask App on port 5000")
        app.run(debug=True, port=5001)
    except Exception as e:
        print("❌ ERROR: Flask App failed to run:", e)

