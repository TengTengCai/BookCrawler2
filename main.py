import argparse
import logging

from crawler import BookCrawler
from db_controller import MongoDataBase

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main():
    mongo_uri = "mongodb://tianjun:1qaz2WSX@120.25.170.193:27017/"
    mongo_db = MongoDataBase(mongo_uri)
    for _ in range(args.thread):
        bc = BookCrawler(mongo_db, args.remote)
        bc.start()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--thread', '-t', type=int, default=5, help='thread numbers')
    parser.add_argument('--remote', '-r', default='', help="remote uri")
    args = parser.parse_args()
    main()
