"""
Example uses Open Library Books API (https://openlibrary.org/dev/docs/api/books)
"""
import requests

from rest_client_gen.generator import MetadataGenerator
from rest_client_gen.registry import ModelRegistry
from testing_tools.pprint_meta_data import pretty_format_meta
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

    gen = MetadataGenerator()
    reg = ModelRegistry()
    for data in (search_result, books):
        reg.process_meta_data(gen.generate(*data))
    reg.merge_models(generator=gen)

    print("\n" + "=" * 20, end='')
    for model in reg.models:
        model.generate_name()
    for model in reg.models:
        print(pretty_format_meta(model))
        print("\n" + "=" * 20, end='')


if __name__ == '__main__':
    main()
