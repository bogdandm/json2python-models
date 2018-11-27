import builtins
import io
import sys
import traceback
import weakref
from functools import wraps

open_files = weakref.WeakSet()


def opener(old_open):
    @wraps(old_open)
    def tracking_open(*args, **kw):
        file = old_open(*args, **kw)

        old_close = file.close

        @wraps(old_close)
        def close():
            old_close()
            open_files.remove(file)

        file.close = close
        try:
            file.stack = traceback.extract_stack()
        except Exception as e:
            print(e)

        open_files.add(file)
        return file

    return tracking_open


io.open = opener(io.open)
builtins.open = opener(builtins.open)


def print_open_files():
    if not open_files:
        print("No files are opened", file=sys.stderr)
        return
    print("Opened files:", file=sys.stderr)
    for file in open_files:
        print(
            f'{file.name}:\n'
            f'{"".join(traceback.format_list(file.stack))}',
            file=sys.stderr
        )
