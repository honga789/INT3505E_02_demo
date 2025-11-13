# Deprecation Notice: `/api/v1/books`

We are deprecating **API version v1** for the Books resource and introducing **v2**.

## What is changing?

The Books API under:

- `/api/v1/books`
- `/api/v1/books/{id}`

is now **deprecated** and will be replaced by:

- `/api/v2/books`
- `/api/v2/books/{id}`

The main breaking change in **v2** is in the **create** endpoint:

- In **v1**, the `available` field in the request body was optional and defaulted to `true` when omitted.
- In **v2**, the `available` field is now **required**.

All other operations on the Books resource keep the same behavior, but are now exposed under the `/api/v2/books` prefix.

## Migration details

### Old (v1) request example

```http
POST /api/v1/books
Content-Type: application/json

{
  "title": "Clean Code",
  "author": "Robert C. Martin"
}
````

### New (v2) request example

```http
POST /api/v2/books
Content-Type: application/json

{
  "title": "Clean Code",
  "author": "Robert C. Martin",
  "available": true
}
```

Clients **must** include the `available` field (`true` or `false`) when creating a book via `POST /api/v2/books`.

## Timeline

* **From December 1, 2025**: `/api/v1/books` is considered **deprecated**. It will continue to work but will not receive new features.
* **After March 1, 2026**: `/api/v1/books` may be removed in a later release. New integrations should use `/api/v2/books` only.

## Required actions for developers

* Update your clients to call **`/api/v2/books`** instead of `/api/v1/books`.
* Ensure your JSON payload always includes the `available` field when creating a book.

If you have any questions or need assistance with the migration, please contact the API maintainers at **[hehehe@mail.com](mailto:hehehe@mail.com)**.
