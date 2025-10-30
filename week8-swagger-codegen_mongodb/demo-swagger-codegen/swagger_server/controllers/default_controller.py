import connexion
import six

from swagger_server.models.book import Book  # noqa: E501
from swagger_server.models.book_create import BookCreate  # noqa: E501
from swagger_server import util


def books_get():  # noqa: E501
    """List all books

     # noqa: E501


    :rtype: List[Book]
    """
    return 'do some magic!'


def books_id_delete(id):  # noqa: E501
    """Delete a book by id

     # noqa: E501

    :param id: 
    :type id: int

    :rtype: None
    """
    return 'do some magic!'


def books_id_get(id):  # noqa: E501
    """Get a book by id

     # noqa: E501

    :param id: 
    :type id: int

    :rtype: Book
    """
    return 'do some magic!'


def books_post(body):  # noqa: E501
    """Create a new book

     # noqa: E501

    :param body: 
    :type body: dict | bytes

    :rtype: Book
    """
    if connexion.request.is_json:
        body = BookCreate.from_dict(connexion.request.get_json())  # noqa: E501
    return 'do some magic!'
