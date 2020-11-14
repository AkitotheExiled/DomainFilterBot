import logging

class Logger:
    def __init__(self):
        logging.basicConfig()
        self.log = logging.getLogger(__name__)
        self.log.setLevel(logging.WARNING)
        self.handler = logging.FileHandler("domainfilterbot.log")
        self.handler.setLevel(logging.WARNING)

        self.formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        self.handler.setFormatter(self.formatter)
        self.log.addHandler(self.handler)