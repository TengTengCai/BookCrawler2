import logging

from crawler import BookCrawler
from db_controller import MongoDataBase

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main():
    mongo_uri = ""
    mongo_db = MongoDataBase(mongo_uri)
    for _ in range(3):
        bc = BookCrawler(mongo_db)
        bc.start()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
