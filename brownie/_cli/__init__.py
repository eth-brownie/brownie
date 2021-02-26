from pathlib import Path

import click

cli_folder = Path(__file__).parent.absolute()


class BrownieCLI(click.MultiCommand):
    def list_commands(self, ctx):
        return list(
            sorted(
                f.stem for f in cli_folder.glob("*.py") if f.stem not in ["__init__", "__main__"]
            )
        )

    def get_command(self, ctx, name):
        ns = {}
        fn = cli_folder / Path(f"{name}.py")
        code = compile(fn.read_text(), fn, "exec")
        eval(code, ns, ns)
        return ns["cli"]


@click.command(cls=BrownieCLI, context_settings=dict(help_option_names=["-h", "--help"]))
@click.version_option(message="%(version)s")
def cli():
    pass
