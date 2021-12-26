import logging

from crawler import BookCrawler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    mongo_uri = "mongodb://root:example@127.0.0.1:27017"
    bc = BookCrawler(mongo_uri)
    bc.start()
    pass


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
