# make_zip.py
import zipfile, os

def make_zip():
    with zipfile.ZipFile("cbt_app_final.zip", "w") as z:
        for fname in ["app.py", "utils.py", "requirements.txt", "cbt_app.db"]:
            if os.path.exists(fname):
                z.write(fname)
    print("✅ Created cbt_app_final.zip")

if __name__ == "__main__":
    make_zip()
