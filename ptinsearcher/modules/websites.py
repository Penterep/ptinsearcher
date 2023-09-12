import requests
import re
import urllib
import html

from bs4 import BeautifulSoup

from ptlibs import ptprinthelper, ptmisclib, ptnethelper
from modules import metadata, emails, comments, forms, phones, ip_addresses, urls


def process_website(url: str, args, ptjsonlib: object, extract_types: dict) -> dict:
    """Returns extracted info from <url>"""
    try:
        response = ptmisclib.load_url_from_web_or_temp(url=url, method="POST" if args.post_data else "GET", headers=ptnethelper.get_request_headers(args), proxies={"http": args.proxy, "https": args.proxy}, data=args.post_data, timeout=args.timeout, redirects=args.redirects, verify=False, cache=args.cache_requests)
    except requests.exceptions.RequestException:
        raise requests.exceptions.RequestException

    args.use_json = args.json
    response.encoding = response.apparent_encoding
    content_type = str(response.headers.get("content-type")).split(";")[0]
    ptprinthelper.ptprint(f"Source-Type.................: website", "TITLE", not args.use_json)
    ptprinthelper.ptprint(f"Content-Type................: {content_type}", "TITLE", not args.use_json)
    ptprinthelper.ptprint(f"Status Code.................: {response.status_code}", "TITLE", not args.use_json, end=" ")

    if _stop_on_redirect(response, args):
        return
    else:
        result_data = _scrape_website(response, ptjsonlib, args, extract_types, soup=_get_soup(response.text, response))
        return result_data

def _scrape_website(response, ptjsonlib, args, extract_types: dict, soup=None) -> dict:
        """Extracts <extract_types> from HTML page"""
        result_data = {"url": response.url, "metadata": None, "emails": None, "phones": None, "ip_addresses": None, "abs_urls": None, "internal_urls": None, "internal_urls_with_parameters": None, "external_urls": None, "subdomains": None, "forms": None, "comments": None}
        page_content = urllib.parse.unquote(urllib.parse.unquote(html.unescape(soup.prettify()))) if soup else urllib.parse.unquote(urllib.parse.unquote(html.unescape(response.text)))

        if extract_types["metadata"]:
            result_data["metadata"] = metadata.get_metadata(page_content=page_content)
            ptjsonlib.add_node(ptjsonlib.create_node_object("metadata", None, None, properties={"metadata": result_data["metadata"]}))

        if extract_types["emails"]:
            result_data["emails"] = emails.find_emails(page_content)
            ptjsonlib.add_node(ptjsonlib.create_node_object("emails", None, None, properties={"emails": result_data["emails"]}))

        if extract_types["comments"]:
            result_data["comments"] = comments.find_comments(page_content)
            ptjsonlib.add_node(ptjsonlib.create_node_object("comments", None, None, properties={"comments": result_data["comments"]}))

        if extract_types["phone_numbers"]:
            result_data["phones"] = phones.find_phones(page_content)
            ptjsonlib.add_node(ptjsonlib.create_node_object("phones", None, None, properties={"phones": result_data["phones"]}))

        if extract_types["ip_addresses"]:
            result_data["ip_addresses"] = ip_addresses.find_ip_addresses(page_content)
            ptjsonlib.add_node(ptjsonlib.create_node_object("ip_addresses", None, None, properties={"ip_addresses": result_data["ip_addresses"]}))

        if any([extract_types["internal_urls"], extract_types["external_urls"], extract_types["internal_urls_with_parameters"], extract_types["subdomains"]]):
            result_data["abs_urls"] = urls.find_abs_urls(page_content)
            ptjsonlib.add_node(ptjsonlib.create_node_object("abs_urls", None, None, properties={"abs_urls": result_data["abs_urls"]}))

        if extract_types["internal_urls"] or extract_types["internal_urls_with_parameters"]:
            result_data["internal_urls"] = urls.find_urls_in_response(page_content, r'(href=|src=)[\'"](.+?)[\'"]', response.url, "internal", without_parameters=args.without_parameters)
            ptjsonlib.add_node(ptjsonlib.create_node_object("internal_urls", None, None, properties={"internal_urls": result_data["internal_urls"]}))

        if extract_types["internal_urls_with_parameters"]:
            result_data["internal_urls_with_parameters"] = _sort(urls._find_internal_parameters(result_data["internal_urls"], group_parameters=args.group_parameters))
            ptjsonlib.add_node(ptjsonlib.create_node_object("internal_urls_with_parameters", None, None, properties={"internal_urls_with_parameters": result_data["internal_urls_with_parameters"]}))

        if extract_types["external_urls"]:
            result_data['external_urls'] = urls.find_urls_in_response(page_content, r'(href=|src=)[\'"](.+?)[\'"]', response.url, "external", without_parameters=args.without_parameters)
            ptjsonlib.add_node(ptjsonlib.create_node_object("external_urls", None, None, properties={"external_urls": result_data["external_urls"]}))

        if extract_types["subdomains"]:
            result_data['subdomains'] = urls.find_urls_in_response(page_content, r'(href=|src=)[\'"](.+?)[\'"]', response.url, "subdomain", without_parameters=args.without_parameters)
            ptjsonlib.add_node(ptjsonlib.create_node_object("subdomains", None, None, properties={"subdomains": result_data["subdomains"]}))

        if not extract_types["internal_urls"]:
            result_data["internal_urls"] = None

        if soup:
            if extract_types["forms"]:
                result_data["forms"] = forms.get_forms(soup)
                ptjsonlib.add_node(ptjsonlib.create_node_object("form", None, None, properties={"forms": result_data["forms"]}))

        return result_data

def parse_robots_txt(response):
    allow = list({pattern.lstrip() for pattern in re.findall(r"^Allow: ([\S ]*)", response.text, re.MULTILINE)})
    disallow = list({pattern.lstrip() for pattern in re.findall(r"^Disallow: ([\S ]*)", response.text, re.MULTILINE)})
    sitemaps = re.findall(r"[Ss]itemap: ([\S ]*)", response.text, re.MULTILINE)
    test_data = {"allow": allow, "disallow": disallow, "sitemaps": sitemaps}

    parsed_url = urllib.parse.urlparse(response.url)
    internal_urls = []
    for section_header in test_data.values():
        for finding in section_header:
            parsed_finding = urllib.parse.urlparse(finding)
            if not parsed_finding.netloc:
                full_path = urllib.parse.urlunparse((parsed_url[0], parsed_url[1], parsed_finding[2], "", "", ""))
            else:
                full_path = finding
            internal_urls.append(full_path)
    return internal_urls


def _sort(url_list):
    return sorted(url_list, key=lambda k: k['url'])

def _get_soup(string, response):
    if "xml" in response.headers['Content-Type'] or response.url.endswith("xml"):
        return None
    soup = BeautifulSoup(string, "lxml")
    bdos = soup.find_all("bdo", {"dir": "rtl"})
    for item in bdos:
        item.string.replace_with(item.text[::-1])
    return soup


def _stop_on_redirect(response, args):
    if response.is_redirect and not args.redirects:
        if response.headers.get("location"):
            ptprinthelper.ptprint(f"[redirect] -> {ptprinthelper.get_colored_text(response.headers['location'], 'INFO')}", "", not args.use_json)
        if not response.headers.get("location"):
            ptprinthelper.ptprint(" ", "", not args.use_json)
        ptprinthelper.ptprint("Redirects disabled, not following", "ERROR", not args.use_json, newline_above=True)
        return True
    elif args.redirects and response.history:
        ptprinthelper.ptprint(f"[redirected] -> {ptprinthelper.get_colored_text(response.history[-1].headers['location'], 'INFO')}", "", not args.use_json)
    else:
        ptprinthelper.ptprint(" ", "", not args.use_json)

