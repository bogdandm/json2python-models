import requests

from rest_client_gen.generator import Generator
from rest_client_gen.registry import ModelRegistry
from rest_client_gen.utils import json_format
from testing_tools.pprint_meta_data import pprint_gen
from testing_tools.real_apis import dump_response


session = requests.Session()


def search(s: str) -> dict:
    print(f"Search {s}")
    return session.get("http://openlibrary.org/search.json", params={
        'q': s
    }).json()


def get_book(isbn: str) -> dict:
    isbn = f"ISBN:{isbn}"
    print(f"Get {isbn}")
    return session.get("https://openlibrary.org/api/books", params={
        'bibkeys': isbn,
        'jscmd': 'details',
        'format': 'json'
    }).json()[isbn]


def main():
    SYMBOL = "The Lord of the Rings"

    search_result = search(SYMBOL)
    dump_response("openlibrary", "search", search_result)
    search_result = search_result['docs']

    books = [
        get_book(item['isbn'][0])
        for item in search_result
        if item.get('isbn', None)
    ]
    dump_response("openlibrary", "book", books[0])

    gen = Generator()
    reg = ModelRegistry()
    for data in (search_result, books):
        fields = gen.generate(*data)

        for s in pprint_gen(fields):
            print(s, end='')
        print('\n' + '-' * 10, end='')

        model = reg.register(fields)
        for s in pprint_gen(model):
            print(s, end='')
        print('\n' + '-' * 10, end='')


if __name__ == '__main__':
    main()
