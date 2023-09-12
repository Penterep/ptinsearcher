#!/usr/bin/python3
"""
    Copyright (c) 2023 Penterep Security s.r.o.

    ptinsearcher - Source information extractor

    ptinsearcher is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    ptinsearcher is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with ptinsearcher. If not, see <https://www.gnu.org/licenses/>.
"""

import argparse
import os
import re
import sys; sys.path.append(__file__.rsplit("/", 1)[0])
import urllib

import requests

from _version import __version__

from ptlibs import ptmisclib, ptjsonlib, ptprinthelper
from modules import websites, files, metadata, results


class PtInsearcher:
    def __init__(self, args):
        self.ptjsonlib              = ptjsonlib.PtJsonLib()
        self.use_json               = args.json
        self.extract_types          = self._get_extract_types(args.extract)
        self.domain                 = self._get_domain(args.domain)
        self.url_list               = list(dict.fromkeys(self._get_url_list(args)))
        self.grouping               = args.grouping
        self.grouping_complete      = args.grouping_complete
        self.group_parameters       = args.group_parameters
        self.without_parameters     = args.without_parameters
        self.output_file            = args.output
        self.output_parts           = args.output_parts
        self.file_handler           = open(self.output_file, "w") if args.output and not args.output_parts else None

        args.use_json = args.json
        args.file_handle = open(self.output_file, "w") if args.output and not args.output_parts else None
        if args.output and not args.output_parts:
            args.file_handle = open(args.output, "w")

        self._check_args_combination(args)

    def run(self, args):
        list_of_results = []
        for index, source in enumerate(self.url_list):
            position = f'[{index+1}/{len(self.url_list)}]' if len(self.url_list) > 1 else ""
            ptprinthelper.ptprint(f"Provided source.............: {source} {position}", "TITLE", not self.use_json, colortext=True, newline_above=True if len(self.url_list) > 1 and index != 0 else False)

            if self._is_website(source):
                try:
                    result_dict = websites.process_website(source, args, self.ptjsonlib, self.extract_types)
                    if result_dict: list_of_results.append(result_dict)
                except requests.exceptions.RequestException:
                    if len(self.url_list) > 1: ptprinthelper.ptprint("Server not responding", "ERROR", not self.use_json); continue
                    else: self.ptjsonlib.end_error("Server not responding", self.use_json)

            elif self._is_file(source):
                result = files.process_file(os.path.abspath(source), args, self.ptjsonlib, extract_types=self.extract_types)
                if result: list_of_results.append(result)

            else:
                if len(self.url_list) > 1:
                    ptprinthelper.ptprint("Provided source is neither a file or a valid URL", "ERROR")
                    continue
                else:
                    self.ptjsonlib.end_ok("Provided source is neither a file or a valid URL", self.use_json)


            if not self.use_json and list_of_results:
                if not self.grouping and not self.grouping_complete:
                    results.print_result([list_of_results[-1]], args)


        if not self.use_json and list_of_results:
            if self.grouping_complete or self.grouping:
                results.print_result(list_of_results, args)

        self.ptjsonlib.set_status("ok")
        ptprinthelper.ptprint(self.ptjsonlib.get_result_json(), "", self.use_json)


    def _check_args_combination(self, args) -> None:
        """Checks whether provided args are in a valid combination"""
        if len(self.url_list) > 1 and self.use_json:
            self.ptjsonlib.end_error("Cannot test more than 1 domain while --json parameter is present", "ERROR")
        if any([args.grouping, args.grouping_complete]) and self.use_json:
            self.ptjsonlib.end_error("Cannot use -g or -gc parameters while --json parameter is present", self.use_json)
        if args.grouping and args.grouping_complete:
            self.ptjsonlib.end_error("Cannot use both -g and -gc parameters together", self.use_json)
        if args.output_parts and not args.output:
            self.ptjsonlib.end_error("Missing --output parameter", self.use_json)
        if args.url and args.file:
            self.ptjsonlib.end_error("Cannot use --url and --file parameter together", self.use_json)
        if args.domain and not args.file:
            self.ptjsonlib.end_error("--file required to use with --domain", self.use_json)
        if not args.url and not args.file:
            self.ptjsonlib.end_error("--url or --file parameter required", self.use_json)
        if self.extract_types["metadata"]:
            try:
                metadata.exiftool_is_executable()
            except PermissionError as e:
                self.ptjsonlib.end_error(str(e), self.use_json)

    def _is_file(self, source: str) -> bool:
        """Check whether the provided source is an existing file or not"""
        return os.path.isfile(source)

    def _is_website(self, source: str) -> bool:
        """Check whether the provided source is a website or not"""
        regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?' # optional portS
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        return regex.match(source)

    def _get_domain(self, domain: str) -> str:
        if domain and not re.match("https?:\/\/", domain):
            self.ptjsonlib.end_error("Scheme required for --domain parameter", self.use_json)
        if domain and not domain.endswith("/"):
            domain += "/"
        return domain

    def _get_url_list(self, args) -> list:
        if args.file:
            try:
                url_list = self._read_file(args.file, args.domain)
            except FileNotFoundError:
                self.ptjsonlib.end_error(f"File not found {os.path.join(os.getcwd(), args.file)}", self.use_json)
        elif args.url:
            url_list = args.url
        return url_list

    def _read_file(self, filepath, domain) -> list:
        target_list = []
        domain = self._adjust_domain(domain)
        with open(filepath, "r") as file:
            for line in file:
                line = line.strip("\n")
                if domain:
                    path = urllib.parse.urlparse(line).path
                    while path.startswith("/"): path = path[1:]
                    while path.endswith("/"): path = path[:-1]
                    if not path: continue
                    target_list.append(domain + path)
                else:
                    if re.match('https?:\/\/', line):
                        target_list.append(line)
        return target_list

    def _adjust_domain(self, domain: str) -> str:
        """Adjusts provided <domain>"""
        o = urllib.parse.urlparse(domain)
        self._check_scheme(o.scheme)
        return domain + "/" if not o.path.endswith("/") else domain

    def _check_scheme(self, scheme: str) -> None:
        """Checks whether provided scheme is valid"""
        if not re.match("http[s]?$", scheme):
            self.ptjsonlib.end_error(f"Missing or invalid scheme, supported schemes are: [HTTP, HTTPS]", self.use_json)

    def _get_extract_types(self, extract_str: str) -> dict:
        allowed_letters = {
            "E": "emails",
            "S": "subdomains",
            "C": "comments",
            "F": "forms",
            "U": "internal_urls",
            "X": "external_urls",
            "P": "phone_numbers",
            "M": "metadata",
            "I": "ip_addresses",
            "Q": "internal_urls_with_parameters",
            "A": "all"
        }
        extract_types = {
            "emails": None,
            "comments": None,
            "forms": None,
            "internal_urls": None,
            "external_urls": None,
            "internal_urls_with_parameters": None,
            "phone_numbers": None,
            "ip_addresses": None,
            "metadata": None,
            "subdomains": None,
            "all": None,
        }
        for char in extract_str:
            char = char.upper()
            if char in allowed_letters.keys():
                extract_types.update({allowed_letters[char]: True})
                if char == "A":
                    for i in extract_types:
                        extract_types[i] = True
            else:
                self.ptjsonlib.end_error(f"Invalid parameter '{char}' in --extract argument, allowed characters ({''.join(allowed_letters.keys())})", self.use_json)
        return extract_types


def get_help():
    return [
        {"description": ["Source information extractor"]},
        {"usage": ["ptinsearcher <options>"]},
        {"usage_example": [
            "ptinsearcher -u https://www.example.com/",
            "ptinsearcher -u https://www.example.com/ --extract E        # Dump emails",
            "ptinsearcher -u https://www.example.com/ --extract UQX      # Dump internal URLs, internal URLs w/ parameters, external URLs",
            "ptinsearcher -f url_list.txt",
            "ptinsearcher -f url_list.txt --grouping                     ",
            "ptinsearcher -f url_list.txt --grouping-complete            "
        ]},
        {"options": [
            ["-u",  "--url",                    "<url>",            "Test URL"],
            ["-f",  "--file",                   "<file>",           "Load URL list from file"],
            ["-d",  "--domain",                 "<domain>",         "Domain - merge domain with filepath. Use when wordlist contains filepaths (e.g. /index.php)"],
            ["-e",  "--extract",                "<extract>",        "Set specific data to extract:"], #Specify data to extract [A, E, S, C, F, I, P, U, Q, X, M, T] (default A)
            ["",  "",                           "   A",             "    Extract All (extract everything; default option)"],
            ["",  "",                           "   E",             "    Extract Emails"],
            ["",  "",                           "   S",             "    Extract Subdomains"],
            ["",  "",                           "   C",             "    Extract Comments"],
            ["",  "",                           "   F",             "    Extract Forms"],
            ["",  "",                           "   I",             "    Extract IP addresses"],
            ["",  "",                           "   P",             "    Extract Phone numbers"],
            ["",  "",                           "   U",             "    Extract Internal urls"],
            ["",  "",                           "   Q",             "    Extract Internal urls with parameters"],
            ["",  "",                           "   X",             "    Extract External urls"],
            ["",  "",                           "   M",             "    Extract Metadata"],
            ["-g",  "--grouping",               "",                 "Group findings from multiple sources into one table"],
            ["-gc", "--grouping-complete",      "",                 "Group and merge findings from multiple sources into one result"],
            ["-gp", "--group-parameters",       "",                 "Group URL parameters"],
            ["-wp", "--without-parameters",     "",                 "Without URL parameters"],
            ["-op", "--output-parts",           "",                 "Save each extract-type to separate file"],
            ["-o",  "--output",                 "<output>",         "Save output to file"],
            ["-p",  "--proxy",                  "<proxy>",          "Set proxy (e.g. http://127.0.0.1:8080)"],
            ["-T",  "--timeout",                "<timeout>",        "Set timeout"],
            ["-c",  "--cookie",                 "<cookie=value>",   "Set cookie"],
            ["-ua", "--user-agent",             "<user-agent>",     "Set User-Agent"],
            ["-H",  "--headers",                "<header:value>",   "Set custom header(s)"],
            ["-r",  "--redirects",              "",                 "Follow redirects (default False)"],
            ["-C",  "--cache",                  "",                 "Cache requests (load from tmp in future)"],
            ["-v",  "--version",                "",                 "Show script version and exit"],
            ["-h",  "--help",                   "",                 "Show this help message and exit"],
            ["-j",  "--json",                   "",                 "Output in JSON format"],
        ]
        }]


def parse_args():
    parser = argparse.ArgumentParser(add_help=False, usage=f"{SCRIPTNAME} <options>")
    parser.add_argument("-u",  "--url",                type=str, nargs="+")
    parser.add_argument("-d",  "--domain",             type=str)
    parser.add_argument("-f",  "--file",               type=str)
    parser.add_argument("-e",  "--extract",            type=str, default="A")
    parser.add_argument("-pd", "--post-data",          type=str)
    parser.add_argument("-o",  "--output",             type=str)
    parser.add_argument("-p",  "--proxy",              type=str)
    parser.add_argument("-T",  "--timeout",            type=int)
    parser.add_argument("-c",  "--cookie",             type=str, nargs="+")
    parser.add_argument("-ua", "--user-agent",         type=str, default="Penterep Tools")
    parser.add_argument("-H",  "--headers",            type=ptmisclib.pairs, nargs="+")
    parser.add_argument("-r",  "--redirects",          action="store_true")
    parser.add_argument("-op", "--output-parts",       action="store_true")
    parser.add_argument("-g",  "--grouping",           action="store_true")
    parser.add_argument("-gc", "--grouping-complete",  action="store_true")
    parser.add_argument("-gp", "--group-parameters",   action="store_true")
    parser.add_argument("-wp", "--without-parameters", action="store_true")
    parser.add_argument("-C",  "--cache-requests",     action="store_true")
    parser.add_argument("-j",  "--json",               action="store_true")
    parser.add_argument("-v",  "--version",            action="version", version=f"%(prog)s {__version__}", help="show version")

    if len(sys.argv) == 1 or "-h" in sys.argv or "--help" in sys.argv:
        ptprinthelper.help_print(get_help(), SCRIPTNAME, __version__)
        sys.exit(0)
    args = parser.parse_args()
    ptprinthelper.print_banner(SCRIPTNAME, __version__, args.json, space=0)
    return args


def main():
    global SCRIPTNAME
    SCRIPTNAME = "ptinsearcher"
    requests.packages.urllib3.disable_warnings()
    args = parse_args()
    script = PtInsearcher(args)
    script.run(args)


if __name__ == "__main__":
    main()
