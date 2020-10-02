import logging
import os
import stat
import sys
import typing as t

import click

from chickenpy.compiler import compile, ParseError
from chickenpy.vm import Machine

EXIT_FAILURE = 1
EXIT_SUCCESS = 0

log = logging.getLogger("chickenpy")

formatter = logging.Formatter("%(name)s - %(message)s")
handler = logging.StreamHandler()
handler.setFormatter(formatter)

log.addHandler(handler)


def interpret(source_code: str, input: t.Optional[str] = None) -> t.Optional[int]:
    """Compiles source code then runs it in the virtual machine."""
    # Compile code
    try:
        code = compile(source_code)
    except ParseError as e:
        click.echo(message=f"ERROR: {e}", err=True)
        return EXIT_FAILURE

    # Run code
    vm = Machine(code, input)
    result = vm.run()
    click.echo(message=result)
    return EXIT_SUCCESS


@click.command()
@click.option("-f", "--file", type=click.File("r"), default=None, help="The source code to run.")
@click.option("--debug/--no-debug", default=False, envvar="DEBUG", help="Show debug information.")
@click.argument("input", type=str, default="")
def main(file: click.File, debug: bool, input: int) -> int:
    """
    A Python implementation of the chicken esoteric programming language.

    Pass a source file using -f/--file or pipe the source to the program.
    """
    # Debug mode
    if debug:
        log.setLevel(logging.DEBUG)

    # Accept source code from both the --file option and stdin
    # https://stackoverflow.com/a/13443424/11457597
    stdin_mode = os.fstat(sys.stdin.fileno()).st_mode
    if file:
        log.debug(f"Reading source from file: {file.name!r}")
        source_code = file.read()
    elif stat.S_ISFIFO(stdin_mode) or stat.S_ISREG(stdin_mode):
        log.debug("Reading source from pipe/redirect...")
        source_code = click.open_file("-").read()
    else:
        log.debug("Couldn't find source!")
        message = (
            "ERROR: Source code required. Pipe text into the program or pass the --file option."
        )
        click.echo(message=message, err=True)
        return EXIT_FAILURE

    exit_status = interpret(source_code, input)
    return exit_status


if __name__ == "__main__":
    sys.exit(main())
