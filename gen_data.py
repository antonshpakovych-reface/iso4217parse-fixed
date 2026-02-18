import json
import sys
from pathlib import Path

import requests
import iso4217
import csv
import io


GEONAMES_URL = "https://download.geonames.org/export/dump/countryInfo.txt"
NEW_CURRENCY_BY_DEPRECATED = {
    "BGN": "EUR",
    "ANG": "XCG",
}
COUNTRY_WITHOUT_CURRENCY = ["AQ"]


def parse_geonames(symbols_by_currency_alpha3):
    response = requests.get(GEONAMES_URL)
    response.raise_for_status()

    file = io.StringIO(response.text)

    header_names = []
    data_lines = []
    for line in file:
        if line.startswith("#"):
            if line.startswith("#ISO"):
                header_names = line.lstrip("#").strip().split("\t")
        else:
            data_lines.append(line)

    reader = csv.DictReader(data_lines, fieldnames=header_names, delimiter="\t")

    currency_map = {}
    for row in reader:
        if row["ISO"] in COUNTRY_WITHOUT_CURRENCY:
            continue

        currency_alpha3 = row["CurrencyCode"]

        if currency_alpha3 in NEW_CURRENCY_BY_DEPRECATED:
            currency_alpha3 = NEW_CURRENCY_BY_DEPRECATED[currency_alpha3]

        parsed_iso_currency = iso4217.Currency(currency_alpha3)

        if currency_alpha3 in currency_map:
            currency_map[currency_alpha3]["countries"].append(row["ISO"])
        else:
            currency_info = {
                "alpha3": currency_alpha3,
                "code_num": parsed_iso_currency.number,
                "countries": [row["ISO"]] or 0,
                "minor": parsed_iso_currency.exponent or 0,
                "name": parsed_iso_currency.currency_name,
                "symbols": symbols_by_currency_alpha3.get(currency_alpha3, []),
            }
            currency_map[currency_alpha3] = currency_info

    return currency_map


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <output_dir>")
        sys.exit(1)

    output_path = Path(sys.argv[1])
    output_path.mkdir(parents=True, exist_ok=True)

    symbols_path = output_path / "symbols.json"
    symbols_data = {}
    if symbols_path.exists():
        with open(symbols_path, "r", encoding="utf-8") as f:
            symbols_data = json.load(f)

    data = parse_geonames(symbols_data)

    with open(output_path / "data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False, sort_keys=True)

    print(f"Done! Processed {len(data)} currencies.")
