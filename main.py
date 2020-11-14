from src.classes.baseclass import RedditBaseClass
from src.database.database import Subreddits, Posts
import datetime
from datetime import timezone
import praw
from prawcore.exceptions import NotFound, ServerError, RequestException
import time


class DomainFilterBot(RedditBaseClass):

    def __init__(self):
        super().__init__()
        self.user_agent = "DomainFilterBot 1.0 PC SCOOPJR"
        self.reddit = praw.Reddit(username=self.user,
                                  password=self.password,
                                  client_id=self.client,
                                  client_secret=self.secret,
                                  user_agent=self.user_agent)
        self.first_run = False
        self.subs = "+"

    def add_subreddits(self):
        for sub in self.reddit.redditor(self.user).moderated():
            self.add_subreddit(sub.display_name)

    def get_or_add(self, model, **kwargs):
        instance = self.db.session.query(model).filter_by(**kwargs).first()
        if instance:
            return instance
        else:
            try:
                instance = model(**kwargs)
                self.db.session.add(instance)
                self.db.session.commit()
            except Exception:
                self.logger.critical("Error getting or adding", exc_info=True)

    def does_exist(self, model, **kwargs):
        instance = self.db.session.query(model).filter_by(**kwargs).first()
        if instance:
            return True
        else:
            return False

    def print_wikipages(self, sub):
        for page in self.reddit.subreddit(sub).wiki:
            print(page)

    def get_wiki_config(self, sub):
        wiki_info = None
        try:
            wiki_info = self.reddit.subreddit(sub).wiki["banned_domains"].content_md
            print(wiki_info)
        except NotFound:
            self.reddit.subreddit(sub).message("Unable to setup bot",
                                               "You must create a wiki page called 'banned_domains' "
                                               "in order for the bot to continue with its setup.  "
                                               "\nI.E. "
                                               "https://www.reddit.com/r/yoursubreddit/about/wiki/domains\n")
            self.subreddit.remove(sub)
        return wiki_info

    def compare_database_to_moderated(self):
        for sub in self.subreddit:
            is_wiki_setup = self.get_wiki_config(sub)
            if is_wiki_setup is not None:
                instance_check = self.db.session.query(Subreddits).filter_by(name=sub.lower()).first()
                if not instance_check:
                    instance = self.get_or_add(Subreddits, name=sub.lower(), blocked_domains=is_wiki_setup.lower(),
                                               date_added=self.get_utctimestamp())
                    if instance and is_wiki_setup.lower() != instance.blocked_domains:
                        instance.blocked_domains = is_wiki_setup.lower()
                        self.db.session.commit()

        self.config_checked(str(self.get_utctimestamp()))

    def config_checked(self, data):
        with open("config_check.txt", "w+") as f:
            f.write(data)

    def get_utctimestamp(self):
        dt = datetime.datetime.now()
        utc_time = dt.replace(tzinfo=timezone.utc)
        utc_timestamp = utc_time.timestamp()
        return utc_timestamp

    def user_exists(self, user):
        try:
            self.reddit.redditor(user).id
        except NotFound:
            return False
        return True

    def check_user_desc(self, user, keywords):
        if self.words_in_string(keywords, self.reddit.redditor(user).subreddit["public_description"].lower()):
            return True
        else:
            return False

    def check_user_posts(self, user, keywords):
        for post in self.reddit.redditor(user).submissions.hot(limit=5):
            if self.words_in_string(keywords, post.title.lower()):
                return True
        return False

    def remove_post(self, postid):
        sub = self.reddit.submission(postid)
        sub.mod.remove(spam=True)
        msg = """
        Your post has been removed.  \nThis action was performed automatically by a bot.  
        If you believe this action to be in error, 
        contact the moderators through mod mail.\n Come across a bug? \n
        [Contact the developer](https://www.reddit.com/message/compose/?to=ScoopJr)
        """
        sub.mod.send_removal_message(message=msg, type="public")

    def get_last_config_check(self):
        with open("config_check.txt", "w+") as f:
            read_data = f.read()
            return read_data

    def time_to_update_config(self):
        current_time = datetime.datetime.utcnow()
        past_time = self.get_last_config_check()
        if past_time == "":
            return None
        diff = (current_time - datetime.datetime.utcfromtimestamp(int(past_time))).total_seconds()
        if diff >= 86400:
            return True
        else:
            return False

    # thank you Peter Gibson from SO
    def words_in_string(self, word_list, a_string):
        return set(word_list).intersection(a_string.split())

    def main(self):
        while True:
            if self.time_to_update_config() or not self.first_run:
                self.add_subreddits()
                self.compare_database_to_moderated()
                if len(self.subreddit) > 1:
                    self.subs = self.subs.join(self.subreddit)
                else:
                    self.subs = self.subreddit[0]
                self.first_run = True
            try:
                subreddit = self.reddit.subreddit(self.subs)
                print(self.subs)
                for post in subreddit.stream.submissions(skip_existing=True, pause_after=5):
                    if post is None:
                        break
                    print(post.title)
                    if self.user_exists(post.author.name.lower()):
                        sub = self.db.session.query(Subreddits).filter_by(name=post.subreddit.display_name.lower()).first()
                        domains = sub.blocked_domains.split(",")
                        if self.check_user_desc(post.author.name.lower(), domains) or \
                                self.check_user_posts(post.author.name.lower(), domains) and not self.does_exist(Posts, postid=post.id):
                            print(f"Removing {post.title} from {post.subreddit.display_name}")
                            self.remove_post(post.id)
                            self.get_or_add(Posts, postid=post.id, author=post.author.name.lower(),
                                            post_utc=post.created_utc, date_removed=self.get_utctimestamp(),
                                            removal_reason="blocked domain")
                            time.sleep(2)
                            break

            except (ServerError, NotFound, RequestException):
                self.logger.warning("Error has occurred within the API", exc_info=True)


if __name__ == "__main__":
    bot = DomainFilterBot()
    bot.main()
