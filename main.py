import argparse
import logging
import time

from config import Config
from crawler import BookCrawler, IPProxy
from db_controller import MongoDataBase

logging.basicConfig(level=logging.INFO, format="%(asctime)s-%(name)s-%(levelname)s-%(lineno)d:\t %(message)s")
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
    for _ in range(cfg.thread):
        bc = BookCrawler(mongo_db, ip_proxy, cfg.dangdang, cfg.baidu, cfg.remote)
        crawler_list.append(bc)
        bc.start()

    try:
        while True:
            delete_list = []
            for bc in crawler_list:
                if not bc.is_alive():
                    delete_list.append(bc)
            logger.info(f"Delete {len(delete_list)} BookCrawler.")
            for bc in delete_list:
                new_bc = BookCrawler(mongo_db, ip_proxy, cfg.dangdang, cfg.baidu, cfg.remote)
                crawler_list.append(new_bc)
                new_bc.start()
                crawler_list.remove(bc)
            time.sleep(10)
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
