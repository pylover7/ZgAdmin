from pathlib import Path

from pydantic_core import MultiHostUrl


def db_engine(  # noqa: PLR0913
    scheme: str = "sqlite", username: str = "", password: str = "", host: str = "", port: int = 5432, path: str = ""
) -> str:
    match scheme:
        case "postgresql":
            return str(
                MultiHostUrl.build(
                    scheme="postgresql+psycopg", username=username, password=password, host=host, port=port, path=path
                )
            )
        case "mysql":
            return str(
                MultiHostUrl.build(
                    scheme="mysql+pymysql", username=username, password=password, host=host, port=port, path=path
                )
            )
        case _:
            return f"sqlite:////{Path(__file__).parent.parent.parent.joinpath('static', 'zgadmin.sqlite')}"
