

def format_exception(e):
    """Utility method for extracting useful file and line number data from an exception traceback.
    :return: string, formatted with exception type, message, file and line number within which the exception occurred.
    """
    import sys
    import traceback
    exc_type, exc_value, exc_tb = sys.exc_info()
    tb_entries = traceback.extract_tb(exc_tb, None)
    tb = tb_entries[0]
    tb2 = tb_entries[-1]
    return "{}: {}  caught: {}: {} generated:: {}: {}".format(exc_type.__name__, e.args, tb[0], tb[1], tb2[0], tb2[1])
