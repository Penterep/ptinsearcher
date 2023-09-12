import re


def find_ip_addresses(string: str):
    ip_regex = r'(?<![\.\+\-])[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}'
    return sorted(set(re.findall(ip_regex, string)))