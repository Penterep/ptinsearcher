import re


def find_phone_numbers(string: str):
    """Returns list of found phone numbers from <string>"""
    phone_regex = r"(?<![\w\/=\:-])(\(?\+\d{3}\)?[ -]?)?(\d{3}[ -]?)(\d{2,3}[ -]?)(\d{3}|\d{2} \d{2})(?![\w\"\'\/\\.])"
    search_result = re.findall(phone_regex, string)
    return sorted(set([''.join(tuple_result) for tuple_result in search_result]))