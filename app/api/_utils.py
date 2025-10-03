from flask import request
from sqlalchemy import asc, desc

def parse_pagination():
    page = max(int(request.args.get("page", 1)), 1)
    page_size = min(max(int(request.args.get("page_size", 20)), 1), 100)
    return page, page_size

def apply_sorting(query, model, allowed_fields=("id",)):
    sort_str = request.args.get("sort")
    if not sort_str:
        return query
    for part in sort_str.split(","):
        part = part.strip()
        if not part:
            continue
        if ":" in part:
            field, direction = part.split(":", 1)
        else:
            field, direction = part, "asc"
        if field not in allowed_fields:
            continue
        col = getattr(model, field)
        query = query.order_by(asc(col) if direction.lower() == "asc" else desc(col))
    return query

def api_error(code, message, status=400):
    from flask import jsonify
    res = jsonify({"error": {"code": code, "message": message}})
    res.status_code = status
    return res
