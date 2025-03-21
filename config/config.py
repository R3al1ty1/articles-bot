from dataclasses import dataclass
from environs import Env


@dataclass
class TgBot:
    token: str
    admin_ids: list[str]


@dataclass
class Config:
    tg_bot: TgBot


env: Env = Env()

env.read_env()


def load_config(path) -> Config:

    env: Env = Env()
    env.read_env(path)

    return Config(
        tg_bot=TgBot(
            token=env('BOT_TOKEN'),
            admin_ids=list(map(str, env.list('ADMIN_USERNAMES')))
        )
    )
