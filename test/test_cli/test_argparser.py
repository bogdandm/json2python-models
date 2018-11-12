from json_to_models.cli import Cli


def test_help():
    cli = Cli()
    cli.argparser.print_help()
