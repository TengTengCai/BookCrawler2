from dataclasses import dataclass

import yaml


@dataclass
class Dangdang(object):
    username: str
    password: str


@dataclass
class Baidu(object):
    username: str
    password: str


class Config(object):
    mongo_uri: str
    dangdang: Dangdang
    baidu: Baidu
    thread: int
    remote: str

    def __init__(self, config_path):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.mongo_uri = self.config.get("mongo", dict()).get("uri", None)
        dangdang = self.config.get("dangdang", dict())
        d_username = dangdang.get("username", "")
        d_password = dangdang.get("password", "")
        self.dangdang = Dangdang(d_username, d_password)
        baidu = self.config.get("baidu", dict())
        b_username = baidu.get("username", "")
        b_password = baidu.get("password", "")
        self.baidu = Baidu(b_username, b_password)
        crawler_cfg = self.config.get("crawler", dict())
        self.thread = crawler_cfg.get("thread", 1)
        self.remote = crawler_cfg.get("remote", "")
