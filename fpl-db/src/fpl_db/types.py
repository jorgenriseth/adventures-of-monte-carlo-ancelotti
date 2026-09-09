from sqlalchemy import Integer, TypeDecorator

from fpl_db.enums import Position


class PositionType(TypeDecorator):
    impl = Integer
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return value.value if isinstance(value, Position) else value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return Position(value)
