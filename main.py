import argparse
import logging

from config import Config
from crawler import BookCrawler, IPProxy
from db_controller import MongoDataBase

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main():
    cfg = Config(args.config)
    if args.thread:
        cfg.thread = args.thread
    if args.remote:
        cfg.remote = args.remote
    mongo_db = MongoDataBase(cfg.mongo_uri)
    ip_proxy = IPProxy()
    crawler_list = []
    try:
        for _ in range(cfg.thread):
            bc = BookCrawler(mongo_db, cfg.dangdang, cfg.baidu, cfg.remote)
            crawler_list.append(bc)
            bc.start()
            bc.join()
    except KeyboardInterrupt as e:
        logger.exception(e)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--thread', '-t', type=int, default=None, help='thread numbers')
    parser.add_argument('--remote', '-r', default='', help="remote uri")
    parser.add_argument('--config', '-c', default='./config.yml', help="config path")
    args = parser.parse_args()
    main()
