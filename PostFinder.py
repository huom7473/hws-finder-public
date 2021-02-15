import praw
import json
import pickle
import time
import re
from collections import deque
from datetime import datetime

def log_timestamp():
    return datetime.now().strftime("%Y.%m.%d:%H:%M:%S")
    
class PostFinder:
    def __init__(self, config_file="config.json", pickle_file=".processed.pickle", subreddit="hardwareswap"):
        self.load_config(config_file)
        
        self.logfile = open(self.config["log_file"], 'a') if self.config["log_file"] else None
        self.subreddit = subreddit
        
        self.pickle_file = pickle_file
        try:
            with open(pickle_file, 'rb') as f:
                self.processed = pickle.load(f)
        except FileNotFoundError:
            print("Pickle file not found - initializing a new one.")            
            self.processed = deque(10*[None], 10)
        except:
            print("Error unpickling processed post list - initializing a new one.")
            self.processed = deque(10*[None], 10)
        
        self.reddit = praw.Reddit(client_id=self.config["client_id"], client_secret=self.config["client_secret"],
                             user_agent=self.config["user_agent"])

    def __enter__(self):
        return self
    
    def __exit__(self, e_type, e_val, tb):
        self.log("exiting")
        if self.logfile:
            self.logfile.close()
            
        with open(self.pickle_file, 'wb') as f:
            pickle.dump(self.processed, f)

    def load_config(self, config_file="config.json"):
        with open(config_file) as f:
            self.config = json.load(f)

    def log(self, string):
        if self.logfile:
            self.logfile.write(f"{log_timestamp()}: {string}\n")
            
    def _process_post(self, post):
        title_re = re.compile(r'\[([A-Z-]*)\]\s*\[H\]\s*(.*?)\s*\[W\]\s*(.*)')
        # group 1: Location
        # group 2: [H] contents
        # group 3: [W] contents
        match = title_re.match(post.title)
        self.processed.appendleft(post.id)
        if (match and any(item == "*" or item.lower() in match.group(2).lower() for item in self.config["want"])
           and any(item == "*" or item.lower() in match.group(3).lower() for item in self.config["have"])):
            return {"link": "https://www.reddit.com"+post.permalink, "body": post.selftext, "title": post.title, "id": post.id, "matched": True}

        return {"link": "https://www.reddit.com"+post.permalink, "body": post.selftext, "title": post.title, "id": post.id, "matched": False}
    
    def get_posts(self):
        matched_posts = []
        unmatched_posts = []
        subreddit = self.reddit.subreddit(self.subreddit)

        error_message_printed = False
        while True:
            try:
                latest_posts = list(subreddit.new(limit=5))
                if error_message_printed:
                    print("Reestablished connection to Reddit API.")
                break
            except Exception as e:
                if not error_message_printed:
                    error_message_printed = True
                    print(f"Exception encountered while getting new posts: {e}. Retrying until success...")
                    self.log("exception {e} in call to subreddit.new")
                time.sleep(3)
        
        # print([post.id for post in latest_posts])
        # print([post.id in self.processed for post i latest_posts])
        
        if not any(post.id not in self.processed for post in latest_posts):
            return None
        
        for post in latest_posts:
            if post.id not in self.processed:
                post_details = self._process_post(post)
                if post_details["matched"]:
                    matched_posts.append(post_details)
                else:
                    unmatched_posts.append(post_details)
        return (matched_posts, unmatched_posts)
    
def _main():
    with PostFinder() as pf:
        print(pf.get_posts())
    
if __name__ == "__main__":
    _main()
