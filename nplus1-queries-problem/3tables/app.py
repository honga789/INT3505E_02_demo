from flask import Flask, request, jsonify, abort, g

app = Flask(__name__)


roles = [
    {"id": 1, "role_name": "admin"},
    {"id": 2, "role_name": "librarian"},
    {"id": 3, "role_name": "member"},
    {"id": 4, "role_name": "guest"},
]
users = [{"id": i, "name": f"User {i}", "role_id": (i % 4) + 1} for i in range(1, 201)]
contacts = [{"id": i, "user_id": i, "email": f"user{i}@example.com"} for i in range(1, 201)]


@app.before_request
def _reset_counter():
    g.query_count = 0

def query_users(limit: int):
    g.query_count += 1  # one query to list users
    return users[:limit]

def query_roles_by_ids(role_ids):
    g.query_count += 1  # one batched query
    role_set = set(role_ids)
    return {r["id"]: r for r in roles if r["id"] in role_set}

def query_contacts_by_user_ids(user_ids):
    g.query_count += 1  # one batched query
    uid_set = set(user_ids)
    return {c["user_id"]: c for c in contacts if c["user_id"] in uid_set}


@app.get("/users")
def list_users():
    limit = request.args.get("limit", default=10, type=int)
    limit = max(1, min(limit, len(users)))
    subset = query_users(limit)

    includes = {p.strip().lower() for p in request.args.get("include", "").split(",") if p.strip()}
    data = []

    role_map = {}
    contact_map = {}
    if {"role", "roles"} & includes:
        role_ids = [u["role_id"] for u in subset]
        role_map = query_roles_by_ids(role_ids)
    if {"contact", "contacts"} & includes:
        user_ids = [u["id"] for u in subset]
        contact_map = query_contacts_by_user_ids(user_ids)

    for u in subset:
        item = {
            "id": u["id"],
            "name": u["name"],
            "role_id": u["role_id"],
        }
        if role_map:
            r = role_map.get(u["role_id"])
            item["role_name"] = r["role_name"] if r else None
        if contact_map:
            c = contact_map.get(u["id"])
            item["email"] = c["email"] if c else None 
        data.append(item)

    return jsonify({"data": data, "meta": {"limit": limit, "queries_executed": g.query_count}})

@app.get("/users/<int:user_id>")
def get_user(user_id: int):
    for u in users:
        if u["id"] == user_id:
            return jsonify({"data": u})
    abort(404, description="user not found")


@app.get("/roles/<int:role_id>")
def get_role(role_id: int):
    for r in roles:
        if r["id"] == role_id:
            return jsonify({"data": r})
    abort(404, description="role not found")


@app.get("/contacts")
def get_contact_by_user():
    user_id = request.args.get("user_id", type=int)
    if user_id is None:
        return jsonify({"error": "missing 'user_id'"}), 400
    for c in contacts:
        if c["user_id"] == user_id:
            return jsonify({"data": c})
    abort(404, description="contact not found")


@app.errorhandler(404)
def _not_found(err):
    return jsonify({"error": {"code": 404, "message": err.description}}), 404

if __name__ == "__main__":
    app.run(port=5000, debug=True)
