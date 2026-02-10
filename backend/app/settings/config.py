import configparser
from pathlib import Path

from app.settings import settings

pay_path = Path(settings.CONFIG_PATH).joinpath("pay.ini")
config_path = Path.joinpath(Path(__file__).parent.parent.parent, "config", "config.yml")


class Config:
    def __init__(self, path: Path):
        self.config = configparser.ConfigParser()
        self.path = path
        # 确保配置文件存在
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.touch()
        self.config.read(self.path, encoding='utf-8')

    def get_config(self, section, option, fallback=None):
        if not self.config.has_section(section):
            return fallback
        if not self.config.has_option(section, option):
            return fallback
        return self.config.get(section, option)

    def set_config(self, section, option, value):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, option, value)
        with open(self.path, 'w', encoding='utf-8') as f:
            self.config.write(f)


pay_config = Config(pay_path)
base_config = Config(Path(settings.CONFIG_PATH).joinpath("base.ini"))

if __name__ == '__main__':
    pay_config = Config(pay_path)
    print(pay_config.get_config('mysql', 'host'))
