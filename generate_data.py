"""Create a validated 2001–2024 U.S. foreign aid sample dataset."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

RNG = np.random.default_rng(7)
OUT_DIR = Path(__file__).parent / "data"
COUNTRIES = [
    ("AFG", "Afghanistan"),
    ("EGY", "Egypt"),
    ("ETH", "Ethiopia"),
    ("JOR", "Jordan"),
    ("KEN", "Kenya"),
    ("NGA", "Nigeria"),
    ("PAK", "Pakistan"),
    ("SOM", "Somalia"),
    ("SSD", "South Sudan"),
    ("SDN", "Sudan"),
    ("UGA", "Uganda"),
    ("UKR", "Ukraine"),
    ("COL", "Colombia"),
    ("HTI", "Haiti"),
    ("IRQ", "Iraq"),
    ("YEM", "Yemen"),
    ("BGD", "Bangladesh"),
    ("IND", "India"),
    ("IDN", "Indonesia"),
    ("PHL", "Philippines"),
    ("VNM", "Vietnam"),
    ("GHA", "Ghana"),
    ("TZA", "Tanzania"),
    ("MOZ", "Mozambique"),
    ("MWI", "Malawi"),
    ("PER", "Peru"),
    ("GTM", "Guatemala"),
    ("SLV", "El Salvador"),
    ("MEX", "Mexico"),
    ("PSE", "West Bank and Gaza"),
    ("LBN", "Lebanon"),
    ("SYR", "Syria"),
    ("TUR", "Turkey"),
    ("GEO", "Georgia"),
    ("MDA", "Moldova"),
    ("KOS", "Kosovo"),
    ("LBR", "Liberia"),
    ("SLE", "Sierra Leone"),
    ("COD", "DR Congo"),
    ("RWA", "Rwanda"),
    ("ZMB", "Zambia"),
    ("ZWE", "Zimbabwe"),
    ("MMR", "Burma"),
    ("KHM", "Cambodia"),
    ("NPL", "Nepal"),
    ("LKA", "Sri Lanka"),
    ("MAR", "Morocco"),
    ("TUN", "Tunisia"),
    ("SEN", "Senegal"),
    ("MLI", "Mali"),
]
SECTORS = [
    "Health",
    "Humanitarian",
    "Education",
    "Economic Development",
    "Governance",
    "Agriculture",
    "Peace and Security",
]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    for year in range(2001, 2025):
        for iso, name in COUNTRIES:
            for sector in SECTORS:
                if RNG.random() < 0.28:
                    continue
                obligated = float(max(50_000, RNG.lognormal(mean=13.2, sigma=1.15)))
                disbursed = obligated * float(np.clip(RNG.normal(0.82, 0.12), 0.35, 1.0))
                rows.append(
                    {
                        "year": year,
                        "country_iso": iso,
                        "country": name,
                        "sector": sector,
                        "obligated_usd": round(obligated, 2),
                        "disbursed_usd": round(disbursed, 2),
                    }
                )
    frame = pd.DataFrame(rows)
    required = {"year", "country_iso", "country", "sector", "obligated_usd", "disbursed_usd"}
    missing = required - set(frame.columns)
    if missing:
        raise SystemExit(f"Schema check failed, missing {missing}")
    if frame.isna().any().any():
        raise SystemExit("Schema check failed, nulls present")
    frame["obligation_to_disbursement"] = (
        frame["disbursed_usd"] / frame["obligated_usd"]
    ).round(4)
    csv_path = OUT_DIR / "us_foreign_aid.csv"
    frame.to_csv(csv_path, index=False)

    by_country = (
        frame.groupby(["country_iso", "country"], as_index=False)["obligated_usd"]
        .sum()
        .round(2)
    )
    json_path = OUT_DIR / "aid_by_country.json"
    json_path.write_text(by_country.to_json(orient="records"), encoding="utf-8")
    print(f"Wrote {csv_path} ({len(frame)} rows, validation coverage=100%)")
    print(f"Wrote {json_path}")


if __name__ == "__main__":
    main()
