import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app, get_db, Base, User, Book, Borrowlist

# ตั้งค่าฐานข้อมูล `library.db`
SQLALCHEMY_DATABASE_URL = "sqlite:///./try.db"  # ใช้ฐานข้อมูลแยกสำหรับการทดสอบ
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override dependency สำหรับการทดสอบเพื่อใช้ฐานข้อมูล `library_test.db`
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
        # ทำให้แน่ใจว่าตารางทั้งหมดถูกสร้างใน `library_test.db`
        Base.metadata.create_all(bind=engine)

    @classmethod
    def tearDownClass(cls):
        # ลบฐานข้อมูลหลังจากทดสอบเสร็จ
        Base.metadata.drop_all(bind=engine)

    def test_create_user(self):
        # ทดสอบการสร้างผู้ใช้ใหม่
        response = client.post(
            "/users/",
            json={"username": "jakkaphat", "fullname": "Wongsriwan"}
        )
        self.assertEqual(response.status_code, 200)

    def test_create_book(self):
        # ทดสอบการสร้างหนังสือใหม่
        response = client.post(
            "/books/",
            json={"title": "The Great Gatsby", "firstauthor": "F. Scott Fitzgerald", "isbn": "9780743273565"}
        )
        self.assertEqual(response.status_code, 200)

    def test_create_borrowlist(self):
        # สร้างผู้ใช้และหนังสือก่อน
        self.test_create_user()
        self.test_create_book()

        # ดึงข้อมูลผู้ใช้และหนังสือที่สร้างขึ้น
        db = SessionLocal()
        user = db.query(User).filter(User.username == "jakkaphat").first()
        book = db.query(Book).filter(Book.title == "The Great Gatsby").first()
        db.close()

        self.assertIsNotNone(user)
        self.assertIsNotNone(book)

        # สร้างรายการยืมหนังสือ
        response = client.post(
            "/borrowlist/",
            json={"user_id": user.id, "book_id": book.id}
        )
        print(response.json())  # พิมพ์รายละเอียดของ response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["user_id"], user.id)
        self.assertEqual(data["book_id"], book.id)
        self.assertIn("id", data)

        # ตรวจสอบในฐานข้อมูลโดยตรง
        db = SessionLocal()
        borrow_record = db.query(Borrowlist).filter(Borrowlist.user_id == user.id, Borrowlist.book_id == book.id).first()
        self.assertIsNotNone(borrow_record)
        self.assertEqual(borrow_record.user_id, user.id)
        self.assertEqual(borrow_record.book_id, book.id)

        # ตรวจสอบว่าหนังสือยังคงอยู่ในฐานข้อมูล
        book_check = db.query(Book).filter(Book.id == book.id).first()
        self.assertIsNotNone(book_check)  # ตรวจสอบว่าหนังสือยังอยู่
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