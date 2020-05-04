"""
Example uses Open Library Books API (https://openlibrary.org/dev/docs/api/books)
"""
import requests

from json_to_models.generator import MetadataGenerator
from json_to_models.models.attr import AttrsModelCodeGenerator
from json_to_models.models.base import generate_code
from json_to_models.models.structure import compose_models
from json_to_models.registry import ModelRegistry
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
    reg.process_meta_data(gen.generate(*search_result), model_name="Search")
    reg.process_meta_data(gen.generate(*books), model_name="Book")
    reg.merge_models(generator=gen)

    print("\n" + "=" * 20)
    for model in reg.models:
        model.generate_name()

    structure = compose_models(reg.models_map)
    print(generate_code(structure, AttrsModelCodeGenerator))


if __name__ == '__main__':
    main()
