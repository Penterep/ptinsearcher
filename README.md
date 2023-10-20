[![penterepTools](https://www.penterep.com/external/penterepToolsLogo.png)](https://www.penterep.com/)


# PTINSEARCHER
> Source information extractor

ptinsearcher is a tool for extracting information from provided sources (websites, files). This tool allows dumping of HTML comments, e-mail addresses, phone numbers, IP addresses, subdomains, HTML forms, links and metadata of documents.

## Installation
```
pip install ptinsearcher
```

## Add to PATH
If you cannot invoke the script in your terminal, its probably because its not in your PATH. Fix it by running commands below.

> Add to PATH for Bash
```bash
echo "export PATH=\"`python3 -m site --user-base`/bin:\$PATH\"" >> ~/.bashrc
source ~/.bashrc
```

> Add to PATH for ZSH
```bash
echo "export PATH=\"`python3 -m site --user-base`/bin:\$PATH\"" >> ~/.zshrc
source ~/.zshrc
```

## Usage examples

```
ptinsearcher -u https://www.example.com/
ptinsearcher -u https://www.example.com/ --extract E        # Dump emails
ptinsearcher -u https://www.example.com/ --extract UQX      # Dump internal URLs, internal URLs w/ parameters, external URLs
ptinsearcher -f url_list.txt
ptinsearcher -f url_list.txt --grouping
ptinsearcher -f url_list.txt --grouping-complete
```

## Options
```
-u   --url                 <url>           Test URL
-f   --file                <file>          Load URL list from file
-d   --domain              <domain>        Domain - merge domain with filepath. Use when wordlist contains filepaths (e.g. /index.php)
-e   --extract             <extract>       Set specific data to extract:
                            A                Extract All (extract everything; default option)
                            E                Extract Emails
                            S                Extract Subdomains
                            C                Extract Comments
                            F                Extract Forms
                            I                Extract IP addresses
                            P                Extract Phone numbers
                            U                Extract Internal urls
                            Q                Extract Internal urls with parameters
                            X                Extract External urls
                            M                Extract Metadata
-g   --grouping                            Group findings from multiple sources into one table
-gc  --grouping-complete                   Group and merge findings from multiple sources into one result
-gp  --group-parameters                    Group URL parameters
-wp  --without-parameters                  Without URL parameters
-op  --output-parts                        Save each extract-type to separate file
-o   --output              <output>        Save output to file
-p   --proxy               <proxy>         Set proxy (e.g. http://127.0.0.1:8080)
-T   --timeout             <timeout>       Set timeout
-c   --cookie              <cookie=value>  Set cookie
-ua  --user-agent          <user-agent>    Set User-Agent
-H   --headers             <header:value>  Set custom header(s)
-r   --redirects                           Follow redirects (default False)
-C   --cache                               Cache requests (load from tmp in future)
-v   --version                             Show script version and exit
-h   --help                                Show this help message and exit
-j   --json                                Output in JSON format
```

## Extract arguments
Specify which data to extract from source
```
A - grab all (default)
E - Emails
S - Subdomains
C - Comments
F - Forms
I - IP addresses
U - Internal URLs
Q - Internal URLs with parameters
X - External URLs
P - Phone numbers
M - Metadata
```

## Dependencies

We use [ExifTool](https://exiftool.org/) to extract metadata.

```
requests
bs4
lxml
pyexiftool
tldextract
magic
ptlibs
```


## Version History
```
1.0.1 - 1.0.2
    - tldextract version fix
1.0.0
    - Script logically divided into relevant submodules
    - Code refactorization
    - Updated for latest ptlibs
0.0.5 - 0.0.7
    - Improved stability
    - Updated help message
    - Replaced  extract parameter for comment extraction from 'H' to 'C'
    - Fixed grouping, spacing, json output
0.0.1 - 0.0.4
    - Alpha releases
```

## License

Copyright (c) 2023 Penterep Security s.r.o.

ptinsearcher is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

ptinsearcher is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with ptinsearcher.  If not, see <https://www.gnu.org/licenses/>.

## Warning

You are only allowed to run the tool against the websites which
you have been given permission to pentest. We do not accept any
responsibility for any damage/harm that this application causes to your
computer, or your network. Penterep is not responsible for any illegal
or malicious use of this code. Be Ethical!