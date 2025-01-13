#!/usr/bin/env python3

import os
import sys
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


def fetch_wayback_urls(domain, output_file=None, years=None, chunk_size=5000, param_filter=False):
    """
    Fetch archived URLs from the Wayback Machine (CDX API) for a given domain,
    with optional pagination, optional time filtering, and optional parameter filtering.

    :param domain:       Domain to query (e.g., "example.com")
    :param output_file:  Name of the output file (or None to print to STDOUT)
    :param years:        Number of years for time-based filtering (int) or None
    :param chunk_size:   Number of results fetched per request (default: 5000)
    :param param_filter: If True, only output URLs containing a parameter from ALLOWED_PARAMS
    """
    base_url = "http://web.archive.org/cdx/search/cdx"

    # Build the base query (URL, output format, fields, collapsing duplicates)
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

    offset = 0
    total_urls_fetched = 0  # Count of actually output URLs
    while True:
        # Construct the paginated URL
        cdx_api_url = (
            f"{cdx_base_api_url}"
            f"&limit={chunk_size}"
            f"&offset={offset}"
        )

        try:
            # Increased timeout to 120s for large queries
            response = requests.get(cdx_api_url, timeout=120)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            print(f"[!] Error fetching domain '{domain}' at offset {offset}: {e}", file=sys.stderr)
            break  # Stop fetching on error

        # The first element is usually the header (e.g. ["original"])
        # so skip it to get the actual URL entries
        raw_urls = data[1:] if len(data) > 1 else []

        # If the chunk is empty, we've reached the end
        if not raw_urls:
            break

        # Convert from list of lists -> list of strings
        chunk_urls = [item[0] for item in raw_urls]

        # Optional parameter filtering
        if param_filter:
            filtered_chunk = [
                url for url in chunk_urls
                if any(param in url for param in ALLOWED_PARAMS)
            ]
        else:
            filtered_chunk = chunk_urls

        # Count how many URLs we actually keep
        chunk_count = len(filtered_chunk)

        # Print or write the filtered URLs
        if output_file:
            with open(output_file, "a", encoding="utf-8") as f:
                for url in filtered_chunk:
                    f.write(url + "\n")
        else:
            for url in filtered_chunk:
                print(url)

        # Increase total fetched by how many we just wrote
        total_urls_fetched += chunk_count

        # If the unfiltered chunk was smaller than 'chunk_size', we are at the end
        if len(chunk_urls) < chunk_size:
            break

        # Otherwise, increase offset for the next iteration
        offset += chunk_size

    # Finally, print how many URLs were output
    print(f"    [*] Total URLs fetched (after filtering): {total_urls_fetched}")


def main():
    """Parse arguments and handle single or multiple domain targets."""
    parser = argparse.ArgumentParser(
        description="Waybaccino: A Python tool to fetch archived URLs "
                    "from the Wayback Machine (CDX API) with pagination "
                    "and optional query parameter filtering."
    )

    parser.add_argument(
        "-sT",
        "--single-target",
        help="Query a single domain (e.g., 'example.com').",
        type=str,
        dest="single_target",
        required=False
    )
    parser.add_argument(
        "-mT",
        "--multiple-targets",
        help="Path to a text file containing multiple domains (one per line).",
        type=str,
        dest="multiple_targets",
        required=False
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Path to an optional output file. (If not set, results are printed to STDOUT.)",
        type=str,
        dest="output_file",
        required=False
    )
    parser.add_argument(
        "-t",
        "--time",
        help="Optional number of years to filter results (e.g. 2 for last 2 years).",
        type=int,
        dest="years",
        required=False,
        default=None
    )
    parser.add_argument(
        "-c",
        "--chunk-size",
        help="Number of results per request (default: 5000). Lower it if you get timeouts.",
        type=int,
        dest="chunk_size",
        required=False,
        default=5000
    )
    parser.add_argument(
        "-p",
        "--params",
        help="Only output URLs that contain at least one known query parameter.",
        action="store_true",
        dest="param_filter",
        required=False
    )

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

        fetch_wayback_urls(
            domain,
            output_file=args.output_file,
            years=args.years,
            chunk_size=args.chunk_size,
            param_filter=args.param_filter
        )

    # Multiple targets
    if args.multiple_targets:
        input_file = args.multiple_targets.strip()

        # Check if the file exists
        if not os.path.exists(input_file):
            sys.exit(f"[!] The file '{input_file}' does not exist.")

        with open(input_file, "r", encoding="utf-8") as f:
            for line in f:
                domain = line.strip()
                if domain:
                    print(f"[+] Fetching archived URLs for: {domain}")
                    if args.years:
                        print(f"    [*] Filtering for last {args.years} year(s)")
                    if args.param_filter:
                        print(f"    [*] Only URLs with known query parameters")

                    fetch_wayback_urls(
                        domain,
                        output_file=args.output_file,
                        years=args.years,
                        chunk_size=args.chunk_size,
                        param_filter=args.param_filter
                    )


if __name__ == "__main__":
    main()
