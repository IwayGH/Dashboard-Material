from backend import create_app
from backend.database import init_db, seed_materials

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        init_db()
        seed_materials()
    print("Menjalankan server di http://127.0.0.1:1981")
    app.run(debug=True, port=1981)