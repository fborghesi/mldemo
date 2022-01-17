import logging
import sys

# create formatter
formatter = logging.Formatter('[%(asctime)s] %(levelname)-6s %(filename)30s:%(lineno)-5s %(message)s')

# set up default logger
root = logging.getLogger()
root.setLevel(logging.INFO)

# create handler
handler = logging.StreamHandler(sys.stderr)
handler.setLevel(logging.INFO)
handler.setFormatter(formatter)

# replace default handler
if root.handlers:
    for handler in root.handlers:
        root.removeHandler(handler)
root.addHandler(handler)


