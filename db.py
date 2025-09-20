from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()
engine = create_engine("sqlite:///cbt.db")
SessionLocal = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(String(50), unique=True, nullable=False)
    face_embedding = Column(Text, nullable=False)

class Progress(Base):
    __tablename__ = "progress"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    lesson = Column(String(100))
    answer = Column(Text)

class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)

def init_db():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    # Seed default admin
    if session.query(Admin).count() == 0:
        default_admin = Admin(username="admin", password="1234")
        session.add(default_admin)
        session.commit()
    # Seed dummy students & progress (face_embedding stored as empty array string)
    if session.query(User).count() == 0:
        u1 = User(school_id="S1001", face_embedding="[]")
        u2 = User(school_id="S1002", face_embedding="[]")
        session.add_all([u1, u2])
        session.commit()
        p1 = Progress(user_id=u1.id, lesson="Lesson 1", answer="Negative: I can't do this → Positive: I'll try step by step")
        p2 = Progress(user_id=u2.id, lesson="Lesson 1", answer="Negative: Nobody likes me → Positive: I have people who care")
        session.add_all([p1, p2])
        session.commit()
    session.close()
