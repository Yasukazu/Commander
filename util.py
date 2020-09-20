# used for string object to compare
import unicodedata

# Thanks to https://stackoverflow.com/a/29247821/13709113
def normalize_caseless(text: str):
    return unicodedata.normalize("NFKD", text.casefold())


def caseless_equal(left: str, right: str) -> bool:
    return normalize_caseless(left) == normalize_caseless(right)
