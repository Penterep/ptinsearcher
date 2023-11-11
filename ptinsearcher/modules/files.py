import re
import magic
import mimetypes

from bs4 import BeautifulSoup

from ptlibs import ptprinthelper
from modules import metadata, emails, comments, forms, phone_numbers, ip_addresses, urls


def process_file(path_to_local_file: str, args, ptjsonlib: object, extract_types: dict) -> dict:
    """Returns extracted info from <filepath>"""
    args.use_json  = args.json
    mimetype       = mimetypes.guess_type(path_to_local_file)[0]
    content_type   = magic.from_file(path_to_local_file)
    is_readable = True if re.findall("text", content_type.lower()) else False
    file_extension = path_to_local_file.split("/")[-1].split(".")[-1] if "." in path_to_local_file.split("/")[-1] else None

    ptprinthelper.ptprint(f"Source-Type.................: file", "INFO", not args.use_json)
    ptprinthelper.ptprint(f"Extension...................: {file_extension.upper()}", "INFO", not args.use_json)
    ptprinthelper.ptprint(f"Magic Identification........: {content_type}", "INFO", not args.use_json)
    ptprinthelper.ptprint(f"MIME Type...................: {mimetype}", "INFO", not args.use_json)

    return _scrape_file(path_to_local_file, is_readable, ptjsonlib, args, extract_types)


def _scrape_file(path_to_local_file: str, is_readable, ptjsonlib, args, extract_types: dict) -> dict:
    """Scrapes extract_types from <filepath>"""
    result_data = {"url": path_to_local_file.rsplit("/")[-1], "metadata": None, "emails": None, "phone_numbers": None, "ip_addresses": None, "abs_urls": None, "internal_urls": None, "internal_urls_with_parameters": None, "external_urls": None, "subdomains": None, "forms": None, "comments": None}

    if extract_types["metadata"]:
        extracted_metadata = metadata.get_metadata(path_to_local_file=path_to_local_file)
        result_data["metadata"] = extracted_metadata

    with open(path_to_local_file, "rb") as file:
        file_content = str(file.read())

        if extract_types["emails"]:
            result_data["emails"] = emails.find_emails(file_content)


        if extract_types["comments"]:
            result_data["comments"] = {}
            #result_data["comments"] = comments.find_comments(file_content)

        if extract_types["phone_numbers"]:
            result_data["phone_numbers"] = phone_numbers.find_phone_numbers(file_content)

        if extract_types["ip_addresses"]:
            result_data["ip_addresses"] = ip_addresses.find_ip_addresses(file_content)

        if any([extract_types["internal_urls"], extract_types["external_urls"], extract_types["internal_urls_with_parameters"], extract_types["subdomains"]]):
            result_data["external_urls"] = urls.find_urls_in_file(file_content)

        if extract_types["subdomains"]:
            result_data["subdomains"] = urls.get_subdomains_from_list(result_data["external_urls"])

        if extract_types["internal_urls_with_parameters"]:
            if args.grouping_complete:
                result_data["internal_urls_with_parameters"] = dict()
            else:
                result_data["internal_urls_with_parameters"] = "Not a HTML file"

        if extract_types["forms"]:
            if mimetypes.guess_type(path_to_local_file)[0] in ["text/html"]:
                soup = _get_soup(file_content)
                result_data["forms"] = forms.get_forms(soup)
            else:
                if args.grouping_complete:
                    result_data["forms"] = dict()
                else:
                    result_data["forms"] = "Not a HTML file"

    return result_data


def _get_soup(string, args):
    if "<!ENTITY".lower() in string.lower():
        ptprinthelper.ptprint(f"Forbidden entities found", "ERROR", not args.use_json, colortext=True)
        return False
    else:
        soup = BeautifulSoup(string, features="lxml")
        bdos = soup.find_all("bdo", {"dir": "rtl"})
        for item in bdos:
            item.string.replace_with(item.text[::-1])
        return soup
