from typing import Optional

from ninja import Schema


class EmailAndPasswordLoginSchema(Schema):
    email: str
    password: str


class TokenLoginSchema(Schema):
    token: str


class UserSchema(Schema):
    first_name: str
    last_name: str
    token: str
    email: str
    image: Optional[str] = None
    type: str
