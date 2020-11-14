from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Data:
    def __init__(self):
        self.engine = create_engine("sqlite:///domaindatabase.db")
        session = sessionmaker(bind=self.engine)
        self.session = session()
        Base.metadata.create_all(self.engine)
        self.commit()

    def commit(self):
        self.session.commit()

    def close(self):
        self.engine.dispose()

class Subreddits(Base):
    __tablename__ = 'subreddit'
    id = Column(Integer(), primary_key=True, autoincrement=True)
    name = Column(String())
    blocked_domains = Column(String())
    date_added = Column(Integer())
    removed_posts = relationship("Posts")

    def __init__(self, name, blocked_domains, date_added):
        self.name = name
        self.blocked_domains = blocked_domains
        self.date_added = date_added


class Posts(Base):
    __tablename__ = 'posts'
    id = Column(Integer(), primary_key=True, autoincrement=True)
    postid = Column(String(10), unique=True)
    author = Column(String())
    post_utc = Column(Integer())
    date_removed = Column(Integer())
    removal_reason = Column(String())
    subreddit_id = Column(Integer(), ForeignKey('subreddit.id'))

    def __init__(self, postid, author, post_utc, date_removed, removal_reason):
        self.postid = postid
        self.author = author
        self.post_utc = post_utc
        self.date_removed = date_removed
        self.removal_reason = removal_reason
