from configparser import ConfigParser
from src.database.database import Data
from src.classes.logger import Logger
import os

temp_path = os.path.dirname(os.path.abspath(__file__))
config = os.path.join(temp_path, "../../config.ini")
print(config)

class RedditBaseClass:
    def __init__(self):
        log = Logger()
        self.logger = log.log
        try:
            self.CONFIG = ConfigParser()
            self.CONFIG.read(config)
        # Retrieving User information from config.ini for PRAW
            self.user = self.CONFIG.get('main', 'USER')
            self.password = self.CONFIG.get('main', 'PASSWORD')
            self.client = self.CONFIG.get('main', 'CLIENT_ID')
            self.secret = self.CONFIG.get('main', 'SECRET')
            self.delay = self.CONFIG.getint('main', 'DELAY')
            self.subreddit = []
            self.debug = bool(self.CONFIG.getboolean('main', 'DEBUG'))

            self.db = Data()
        except Exception:
            self.logger.critical("Error getting or adding", exc_info=True)

    def add_subreddit(self, sub):
        if sub not in self.subreddit:
            self.subreddit.append(sub)

