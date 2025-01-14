# Waybaccino
Waybaccino is a Python tool that uses the Wayback Machine CDX API to query archived URLs of one or more domains.

It supports the following functions:

- Pagination (limit/offset) to process large amounts of data without timeouts.
- Optional time filtering (--time/-t) to get only URLs within the last n calendar years.
- Optional parameter filtering (--params/-p) to output only URLs with certain query parameters (e.g. ?id=, ?q=).
- Optional burp proxy parameter (-bp / --burp-proxy)

## Features
- Single or multiple target mode:
  - Query a single domain
- Query multiple domains from a text file
- Pagination: Ensures that the results are queried in manageable ‘chunks’ (default: 5000 URLs) to reduce timeouts.
- Time filtering: Limit the results to the last n years.
- Parameter filter: Only output URLs that contain certain query parameters (e.g. ?id=).
- Send traffic through the burp suite proxy for deeper/further investigation or using bchecks.

## Installation
- Python3 is required
- clone the repo
```bash
# clone the repo
git clone https://github.com/G0urmetD/Waybaccino.git

# install the dependencies
os
sys
argparse
requests
datetime
```

## Options
```bash
usage: waybaccino.py [-h] [-sT SINGLE_TARGET] [-mT MULTIPLE_TARGETS] [-o OUTPUT_FILE] [-t YEARS] [-c CHUNK_SIZE] [-p] [-bp BURP_PROXY]

Waybaccino with minimal Proxy-Fetch Output.

options:
  -h, --help            show this help message and exit
  -sT SINGLE_TARGET, --single-target SINGLE_TARGET
                        Query a single domain (e.g., 'example.com').
  -mT MULTIPLE_TARGETS, --multiple-targets MULTIPLE_TARGETS
                        Path to a text file containing multiple domains (one per line).
  -o OUTPUT_FILE, --output OUTPUT_FILE
                        Path to an optional output file. (If not set, results are printed to STDOUT.)
  -t YEARS, --time YEARS
                        Optional number of years to filter results (e.g. 2 for last 2 years).
  -c CHUNK_SIZE, --chunk-size CHUNK_SIZE
                        Number of results per request (default: 5000). Lower it if you get timeouts.
  -p, --params          Only output URLs that contain at least one known query parameter.
  -bp BURP_PROXY, --burp-proxy BURP_PROXY
                        Send traffic to burp suite proxy.
```

## Usage
```bash
python3 waybaccino.py [OPTIONS]
```

## Examples
1. Query a domain (without time filter)
```bash
python3 waybaccino.py -sT example.com
```

2. Query of a domain (with time filter of 2 years)
```bash
python3 waybaccino.py -sT example.com -t 2
```

3. Query of several domains
```bash
# file with multiple domains [domains.txt]
example.com
example.org
example.net
```
```bash
python3 waybaccino.py -mT domains.txt
```

4. Use parameter filter
```bash
python3 waybaccino.py -sT example.com -p
```

5. Use proxy parameter
```bash
# burp suite proxy with windows
python3 waybaccino.py -sT example.com -bp http://127.0.0.1:8080

# burp suite proxy with wsl
# add a new listener to burp with your machine ip and another port
python3 waybaccino.py -sT example.com -bp http://<windows-machine-ip>:8082
```

6. Use output parameter
```bash
python3 waybaccino.py -sT example.com -o way-example-com.txt
```

## Parameters
The parameters are hardcoded. These can be customised as required.

```python3
# Hard-coded list of parameters to filter by if -p/--params is set:
ALLOWED_PARAMS = [
    '?q=', '?s=', '?search=', '?id=', '?lang=', '?keyword=', '?query=',
    '?page=', '?keywords=', '?year=', '?view=', '?email=', '?type=', '?name=',
    '?p=', '?month=', '?image=', '?list_type=', '?url=', '?terms=',
    '?categoryid=', '?key=', '?login=', '?begindate=', '?enddate='
]
```

```
?q=
?s=
?search=
?id=
?lang=
?keyword=
?query=
?page=
?keywords=
?year=
?view=
?email=
?type=
?name=
?p=
?month=
?image=
?list_type=
?url=
?terms=
?categoryid=
?key=
?login=
?begindate=
?enddate=
```
