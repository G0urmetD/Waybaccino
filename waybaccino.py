#!/usr/bin/env python3

import os
import sys
import urllib3
import argparse
import requests
import datetime

# Hard-coded list of parameters to filter by if -p/--params is set:
ALLOWED_PARAMS = [
    '?q=', '?s=', '?search=', '?id=', '?lang=', '?keyword=', '?query=',
    '?page=', '?keywords=', '?year=', '?view=', '?email=', '?type=', '?name=',
    '?p=', '?month=', '?image=', '?list_type=', '?url=', '?terms=',
    '?categoryid=', '?key=', '?login=', '?begindate=', '?enddate='
]

# Disable the InsecureRequestWarning that appears when using verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_wayback_urls(domain, years=None, chunk_size=5000, param_filter=False):
    """
    Fetch archived URLs from the Wayback Machine (CDX API) for a given domain,
    with optional pagination, optional time filtering, and optional parameter filtering.

    PHASE 1: We do NOT use a proxy here, so we don't get blocked by Burp.

    Returns:
        A list of URLs (strings).
    """
     # Build the base query (URL, output format, fields, collapsing duplicates)
    base_url = "http://web.archive.org/cdx/search/cdx"
    cdx_base_api_url = (
        f"{base_url}?url={domain}/*"
        "&output=json"
        "&fl=original"
        "&collapse=urlkey"
    )

    # Optional time filtering
    if years and years > 0:
        current_year = datetime.datetime.now().year
        from_year = current_year - years
        to_year = current_year
        cdx_base_api_url += f"&from={from_year}&to={to_year}"

    all_filtered_urls = []
    offset = 0

    while True:
        cdx_api_url = f"{cdx_base_api_url}&limit={chunk_size}&offset={offset}" # Construct the paginated URL

        try:
            # Increased timeout to 120s for large queries
            response = requests.get(cdx_api_url, timeout=120)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            print(f"[!] Error fetching domain '{domain}' at offset {offset}: {e}", file=sys.stderr)
            break # Stop fetching on error

        # The first element is usually the header (e.g. ["original"])
        raw_urls = data[1:] if len(data) > 1 else []
        if not raw_urls:
            # No more data
            break

        chunk_urls = [item[0] for item in raw_urls] # Convert from list of lists -> list of strings

        # Optional parameter filtering
        if param_filter:
            chunk_urls = [
                url for url in chunk_urls
                if any(param in url for param in ALLOWED_PARAMS)
            ]

        all_filtered_urls.extend(chunk_urls)

        if len(raw_urls) < chunk_size:
            break

        offset += chunk_size

    return all_filtered_urls


def get_urls_through_proxy(urls, proxy):
    """
    Phase 2: Sends all URLs via GET request via the specified proxy,
    but only shows a simple progress bar in the terminal.
    """
    proxies = {"http": proxy, "https": proxy}
    total = len(urls)
    total_ok = 0

    for i, url in enumerate(urls, start=1):
        print(f"\r    [*] Proxying {i}/{total}...", end="", flush=True)

        try:
            r = requests.get(url, proxies=proxies, timeout=10, verify=False)
            total_ok += 1
        except Exception:
            pass

    print(f"\n    [*] Finished proxy requests. Successful: {total_ok} / {total}")


def main():
    parser = argparse.ArgumentParser(
        description="Waybaccino: A Python tool to fetch archived URLs "
                    "from the Wayback Machine (CDX API) with pagination "
                    "and optional query parameter filtering."
    )
    parser.add_argument("-sT", "--single-target", type=str, dest="single_target", required=False, help="Query a single domain (e.g., 'example.com').")
    parser.add_argument("-mT", "--multiple-targets", type=str, dest="multiple_targets", required=False, help="Path to a text file containing multiple domains (one per line).")
    parser.add_argument("-o", "--output", type=str, dest="output_file", required=False, help="Path to an optional output file. (If not set, results are printed to STDOUT.)")
    parser.add_argument("-t", "--time", type=int, dest="years", required=False, default=None, help="Optional number of years to filter results (e.g. 2 for last 2 years).")
    parser.add_argument("-c", "--chunk-size", type=int, dest="chunk_size", required=False, default=5000, help="Number of results per request (default: 5000). Lower it if you get timeouts.")
    parser.add_argument("-p", "--params", action="store_true", dest="param_filter", required=False, help="Only output URLs that contain at least one known query parameter.")
    parser.add_argument("-bp","--burp-proxy", type=str, dest="burp_proxy", required=False, default=None, help="Send traffic to burp suite proxy.")

    args = parser.parse_args()

    # Ensure exactly one type of target is provided
    if not args.single_target and not args.multiple_targets:
        parser.error("Please provide either '--single-target' or '--multiple-targets'.")
    if args.single_target and args.multiple_targets:
        parser.error("Please provide only one: '--single-target' OR '--multiple-targets'.")

    # Single target
    if args.single_target:
        domain = args.single_target.strip()
        print(f"[+] Fetching archived URLs for: {domain}")

        if args.years:
            print(f"    [*] Filtering for last {args.years} year(s)")
        if args.param_filter:
            print(f"    [*] Only URLs with known query parameters")

        urls = fetch_wayback_urls(
            domain=domain,
            years=args.years,
            chunk_size=args.chunk_size,
            param_filter=args.param_filter
        )
        print(f"    [*] Total URLs collected: {len(urls)}")

        if args.output_file:
            with open(args.output_file, "a", encoding="utf-8") as f:
                for u in urls:
                    f.write(u + "\n")
        else:
            for u in urls:
                print(u)

        # Optional Phase 2
        if args.burp_proxy:
            print(f"    [*] Sending GET requests to each URL via proxy: {args.burp_proxy}")
            get_urls_through_proxy(urls, args.burp_proxy)

    # Multiple targets
    if args.multiple_targets:
        input_file = args.multiple_targets.strip()
        if not os.path.exists(input_file):
            sys.exit(f"[!] The file '{input_file}' does not exist.")

        with open(input_file, "r", encoding="utf-8") as f:
            domains = [line.strip() for line in f if line.strip()]

        for domain in domains:
            print(f"[+] Fetching archived URLs for: {domain}")
            if args.years:
                print(f"    [*] Filtering for last {args.years} year(s)")
            if args.param_filter:
                print(f"    [*] Only URLs with known query parameters")

            urls = fetch_wayback_urls(
                domain=domain,
                years=args.years,
                chunk_size=args.chunk_size,
                param_filter=args.param_filter
            )
            print(f"    [*] Total URLs collected: {len(urls)}")

            if args.output_file:
                with open(args.output_file, "a", encoding="utf-8") as out_f:
                    for u in urls:
                        out_f.write(u + "\n")
            else:
                for u in urls:
                    print(u)

            if args.burp_proxy:
                print(f"    [*] Sending GET requests to each URL via proxy: {args.burp_proxy}")
                get_urls_through_proxy(urls, args.burp_proxy)


if __name__ == "__main__":
    main()
