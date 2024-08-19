import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app, get_db, Base, User

# ตั้งค่าฐานข้อมูล `user.db`
SQLALCHEMY_DATABASE_URL = "sqlite:///./library.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override dependency สำหรับการทดสอบเพื่อใช้ฐานข้อมูล `user.db`
def override_get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

class TestUserEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # ทำให้แน่ใจว่าตารางทั้งหมดถูกสร้างใน `user.db`
        Base.metadata.create_all(bind=engine)

    def test_create_user(self):
        # ทดสอบการสร้างผู้ใช้ใหม่
        response = client.post(
            "/users/",
            json={"username": "jakkaphat", "fullname": "Wongsriwan"}
        )
        print(response.json())  # พิมพ์รายละเอียดของ response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["username"], "jakkaphat")
        self.assertEqual(data["fullname"], "Wongsriwan")
        self.assertIn("id", data)

        # ตรวจสอบในฐานข้อมูลโดยตรง
        db = SessionLocal()
        user = db.query(User).filter(User.username == "jakkaphat").first()
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "jakkaphat")
        self.assertEqual(user.fullname, "Wongsriwan")
        db.close()

        print(response.status_code)  # แสดง status code
        print(response.text)

if __name__ == "__main__":
    unittest.main(verbosity=2)
