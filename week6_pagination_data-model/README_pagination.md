Offset-based pagination → `offset-limit-paging.py` → `http://localhost:5000/books`
<br>
Page-based pagination → `page-based-paging.py` → `http://localhost:5001/books`
<br>
Cursor-based (keyset) pagination → `cursor-based-paging.py` → `http://localhost:5002/books`


## Test: Offset-based (limit / offset)
- [GET] <http://localhost:5000/books?limit=2&offset=0>  
  ◦ 2 books per page, first window
- [GET] <http://localhost:5000/books?limit=2&offset=2>  
  ◦ 2 books per page, second window
- [GET] <http://localhost:5000/books?search=orwell&limit=2&offset=0>  
  ◦ filter by keyword then paginate

## Test: Page-based (page / page_size)
- [GET] <http://localhost:5001/books?page=1&page_size=2>  
  ◦ page 1, 2 items per page
- [GET] <http://localhost:5001/books?page=2&page_size=3>  
  ◦ page 2, 3 items per page
- [GET] <http://localhost:5001/books>  
  ◦ default: page=1, page_size=5
- [GET] <http://localhost:5001/books?search=orwell&page=1&page_size=2>  
  ◦ search + paginate

## Test: Cursor-based (after token)
- [GET] <http://localhost:5002/books?limit=5>  
  ◦ first page
- [GET] <http://localhost:5002/books?limit=5&after=TOKEN>  
  ◦ next page using `next_cursor` from the previous response
- [GET] <http://localhost:5002/books?search=orwell&limit=3>  
  ◦ search + cursor
