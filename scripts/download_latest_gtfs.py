#!/usr/bin/env python3

import os
import sys
import requests
import pandas as pd
import zipfile
import tempfile
import shutil
import math

from pathlib import Path
GTFS_URL = "https://www.arcgis.com/sharing/rest/content/items/929fbd2dbfbf493ab44935577e8fbff6/data"
OUTPUT_FILE = "gtfs-medellin.zip"

def sort_stop_times(gtfs_zip):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        with zipfile.ZipFile(gtfs_zip, "r") as zf:
            zf.extractall(tmpdir)

        stop_times = tmpdir / "stop_times.txt"

        if not stop_times.exists():
            print("stop_times.txt not found")
            return

        print("Sorting stop_times.txt...")

        df = pd.read_csv(
            stop_times,
            low_memory=False,
            dtype=str,
            keep_default_na=False,
        )

        df["stop_sequence"] = pd.to_numeric(
            df["stop_sequence"],
            errors="coerce"
        )

        df = df.sort_values(
            ["trip_id", "stop_sequence"],
            kind="stable"
        )

        df.to_csv(
            stop_times,
            index=False
        )

        output_zip = str(gtfs_zip).replace(".zip", "_sorted.zip")

        with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in tmpdir.rglob("*"):
                if file.is_file():
                    zf.write(
                        file,
                        file.relative_to(tmpdir)
                    )

        shutil.move(output_zip, gtfs_zip)

        print("stop_times.txt sorted successfully")

def main():
    print(f"Downloading: {GTFS_URL}")

    r = requests.get(
        GTFS_URL,
        stream=True,
        timeout=300,
    )
    r.raise_for_status()
    
    with open(OUTPUT_FILE, "wb") as fh:
        for chunk in r.iter_content(chunk_size=1024 * 1024):
            if chunk:
                fh.write(chunk)

    size_mb = Path(OUTPUT_FILE).stat().st_size / 1024 / 1024
    print(f"Saved {OUTPUT_FILE} ({size_mb:.2f} MB)")

    print("Optimizing GTFS feed...")
    sort_stop_times(OUTPUT_FILE)
    print("Optimization complete")

    with open("latest_gtfs_key.txt", "w") as fh:
        fh.write(datetime.utcnow().strftime("%Y-%m-%d"))

    print("Done")


if __name__ == "__main__":
    main()
