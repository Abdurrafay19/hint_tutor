"""Runs ONE test case against student code. Executed as its own process:

    python -I _worker.py   (request JSON on stdin, result JSON as last stdout line)

This is isolated process execution with a timeout set by the parent. It is not a sandbox.
"""
import io
import json
import sys
import traceback


def main():
    req = json.load(sys.stdin)
    real_stdout = sys.stdout
    sys.stdout = io.StringIO()  # swallow student print() output
    try:
        namespace = {"__name__": "student"}
        exec(compile(req["code"], "student.py", "exec"), namespace)
        fn = namespace.get(req["function"])
        if not callable(fn):
            raise NameError("function '%s' is not defined" % req["function"])
        value = fn(*req["args"])
        result = {"ok": True, "value": json.loads(json.dumps(value, default=repr))}
    except BaseException as exc:  # includes SystemExit and RecursionError
        line = None
        for frame in traceback.extract_tb(exc.__traceback__):
            if frame.filename == "student.py":
                line = frame.lineno
        result = {"ok": False, "error": "%s: %s" % (type(exc).__name__, exc), "line": line}
    finally:
        sys.stdout = real_stdout
    print(json.dumps(result))


if __name__ == "__main__":
    main()
