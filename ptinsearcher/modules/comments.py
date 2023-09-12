import re


def find_comments(string: str):
    """Returns comments from provided string"""
    regex_dict = {"html": [r"<!--[\s\w\W]*?-->"], "css": [r"\/\*[^*]*\*+([^/*][^*]*\*+)*\/"], "js": [r'\/\*[\s\S]+?\*\/']}
    comments = dict()
    for key in regex_dict.keys():
        comments.update({key: []})
        for regex in regex_dict[key]:
            search_result = re.findall(regex, string)
            for item in search_result:
                item = item.strip()
                if item and item not in comments[key]:
                    comments[key].append(item)
    return comments