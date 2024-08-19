import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app, get_db, Base, User, Book

# ตั้งค่าฐานข้อมูล `library.db`
SQLALCHEMY_DATABASE_URL = "sqlite:///./library.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override dependency สำหรับการทดสอบเพื่อใช้ฐานข้อมูล `library.db`
def override_get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

class TestLibraryEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # ทำให้แน่ใจว่าตารางทั้งหมดถูกสร้างใน `library.db`
        Base.metadata.create_all(bind=engine)

    def test_create_book(self):
        # ทดสอบการสร้างหนังสือใหม่
        response = client.post(
            "/books/",
            json={"title": "The Great Gatsby", "firstauthor": "F. Scott Fitzgerald", "isbn": "9780743273565"}
        )
        print(response.json())  # พิมพ์รายละเอียดของ response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["title"], "The Great Gatsby")
        self.assertEqual(data["firstauthor"], "F. Scott Fitzgerald")
        self.assertEqual(data["isbn"], "9780743273565")
        self.assertIn("id", data)

        # ตรวจสอบในฐานข้อมูลโดยตรง
        db = SessionLocal()
        book = db.query(Book).filter(Book.title == "The Great Gatsby").first()
        self.assertIsNotNone(book)
        self.assertEqual(book.title, "The Great Gatsby")
        self.assertEqual(book.firstauthor, "F. Scott Fitzgerald")
        self.assertEqual(book.isbn, "9780743273565")
        db.close()

    def test_delete_book(self):
        # ลบหนังสือที่สร้างขึ้น
        db = SessionLocal()
        book = db.query(Book).first()  # เอาหนังสือตัวแรกในฐานข้อมูล
        book_id = book.id if book else None
        db.close()

        if book_id:
            response = client.delete(f"/books/{book_id}")  # ต้องมี endpoint สำหรับลบ
            print(response.status_code)  # แสดง status code
            self.assertEqual(response.status_code, 204)  # คาดว่า status code จะเป็น 204 No Content

            # ตรวจสอบว่าหนังสือถูกลบจากฐานข้อมูลแล้ว
            db = SessionLocal()
            deleted_book = db.query(Book).filter(Book.id == book_id).first()
            self.assertIsNone(deleted_book)
            db.close()
        else:
            self.fail("No book found to delete.")

if __name__ == "__main__":
    unittest.main(verbosity=2)