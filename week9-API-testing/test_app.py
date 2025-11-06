import datetime
import jwt
from app import app, users, _etag_for, _find_book, generate_token, decode_token, books

def test_etag_for_changes():
    a = [{"title": "A"}]
    b = [{"title": "B"}]
    assert _etag_for(a) != _etag_for(b)

def test_find_book_found_and_missing():
    some_id = books[0]["id"]
    assert _find_book(some_id) is not None
    assert _find_book("nope") is None

def test_generate_token_contains_claims_and_future_exp():
    user = users[0]
    tok = generate_token(user)

    decoded = jwt.decode(tok, app.config["SECRET_KEY"], algorithms=["HS256"])
    assert decoded["user_id"] == user["id"]
    assert decoded["username"] == user["username"]
    assert decoded["role"] == user["role"]

    now_ts = int(datetime.datetime.now(datetime.UTC).timestamp())
    assert decoded["exp"] > now_ts

def test_decode_token_valid_invalid_and_expired():
    user = users[0]
    tok = generate_token(user)
    ok = decode_token(tok)
    assert ok["username"] == user["username"]

    bad = tok[:-2] + "xx"
    assert "error" in decode_token(bad)

    past = datetime.datetime.now(datetime.UTC) - datetime.timedelta(seconds=1)
    expired = jwt.encode(
        {"user_id": user["id"], "username": user["username"], "role": user["role"], "exp": past},
        app.config["SECRET_KEY"],
        algorithm="HS256",
    )
    assert decode_token(expired)["error"] == "Token expired"
