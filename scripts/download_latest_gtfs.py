#!/usr/bin/env python3

import os
import sys
import requests
import pandas as pd
import zipfile
import tempfile
import shutil
import math
import holidays
from datetime import datetime
from pathlib import Path

GTFS_URL = "https://www.arcgis.com/sharing/rest/content/items/929fbd2dbfbf493ab44935577e8fbff6/data"
OUTPUT_FILE = "gtfs-medellin.zip"

def generate_feed_info(gtfs_zip):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        with zipfile.ZipFile(gtfs_zip, "r") as zf:
            zf.extractall(tmpdir)

        today = datetime.today()

        feed_info = pd.DataFrame([
            {
                "feed_publisher_name": "Metro de Medellin",
                "feed_publisher_url": "https://www.metrodemedellin.gov.co",
                "feed_lang": "es",
                "feed_start_date": f"{today.year}0101",
                "feed_end_date": f"{today.year + 1}1231",
                "feed_version": today.strftime("%Y-%m-%d")
            }
        ])

        feed_info.to_csv(
            tmpdir / "feed_info.txt",
            index=False
        )

        output_zip = str(gtfs_zip).replace(
            ".zip",
            "_feedinfo.zip"
        )

        with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in tmpdir.rglob("*"):
                if file.is_file():
                    zf.write(
                        file,
                        file.relative_to(tmpdir)
                    )

        shutil.move(output_zip, gtfs_zip)

        print("feed_info.txt generated")

def generate_calendar_dates():
    """
    Generate GTFS calendar_dates.txt for Colombia.
    """

    current_year = datetime.now().year

    # Generate from current year through 1 years ahead
    start_year = current_year
    end_year = current_year + 1

    co_holidays = holidays.CO(
        years=range(start_year, end_year)
    )

    rows = []

    for holiday_date in sorted(co_holidays.keys()):
        date_str = holiday_date.strftime("%Y%m%d")

        # Holiday service operates
        rows.append({
            "service_id": "Domingo-Festivo",
            "date": date_str,
            "exception_type": 1
        })

        weekday = holiday_date.weekday()

        if weekday < 5:
            rows.append({
                "service_id": "Laboral",
                "date": date_str,
                "exception_type": 2
            })
        elif weekday == 5:
            rows.append({
                "service_id": "Sabado",
                "date": date_str,
                "exception_type": 2
            })

    return pd.DataFrame(rows)

def add_calendar_dates(gtfs_zip):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        with zipfile.ZipFile(gtfs_zip, "r") as zf:
            zf.extractall(tmpdir)

        df = generate_calendar_dates()

        df.to_csv(
            tmpdir / "calendar_dates.txt",
            index=False
        )

        output_zip = str(gtfs_zip).replace(".zip", "_calendar.zip")

        with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in tmpdir.rglob("*"):
                if file.is_file():
                    zf.write(
                        file,
                        file.relative_to(tmpdir)
                    )

        shutil.move(output_zip, gtfs_zip)

        print(
            f"Generated calendar_dates.txt with {len(df)} exceptions"
        )

def refresh_calendar(gtfs_zip):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        with zipfile.ZipFile(gtfs_zip, "r") as zf:
            zf.extractall(tmpdir)

        calendar_file = tmpdir / "calendar.txt"

        if not calendar_file.exists():
            print("calendar.txt not found")
            return

        print("Refreshing calendar.txt...")

        df = pd.read_csv(
            calendar_file,
            dtype=str,
            keep_default_na=False
        )

        today = datetime.today()

        df["start_date"] = f"{today.year}0101"
        df["end_date"] = f"{today.year + 1}1231"

        df.to_csv(calendar_file, index=False)

        output_zip = str(gtfs_zip).replace(".zip", "_calendar.zip")

        with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in tmpdir.rglob("*"):
                if file.is_file():
                    zf.write(file, file.relative_to(tmpdir))

        shutil.move(output_zip, gtfs_zip)

        print(
            f"calendar.txt updated to "
            f"{today.year}0101 - {today.year + 1}1231"
        )

def flatten_gtfs_directory(gtfs_dir):
    """
    If the extracted ZIP contains a single top-level folder,
    move its contents into gtfs_dir.
    """
    items = list(Path(gtfs_dir).iterdir())

    # Only one directory and no GTFS files at root
    if len(items) == 1 and items[0].is_dir():
        nested_dir = items[0]

        print(f"Found nested GTFS directory: {nested_dir}")

        for item in nested_dir.iterdir():
            shutil.move(str(item), str(Path(gtfs_dir) / item.name))

        nested_dir.rmdir()

        print("Flattened GTFS directory structure")

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

    # Flatten nested GTFS directory if present
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        with zipfile.ZipFile(OUTPUT_FILE, "r") as zf:
            zf.extractall(tmpdir)

        flatten_gtfs_directory(tmpdir)

        rebuilt_zip = tmpdir / "rebuilt.zip"

        with zipfile.ZipFile(rebuilt_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in tmpdir.rglob("*"):
                if file.is_file() and file != rebuilt_zip:
                    zf.write(file, file.relative_to(tmpdir))

        shutil.move(str(rebuilt_zip), OUTPUT_FILE)

    print("GTFS directory structure normalized")
    
    print("Optimizing GTFS feed...")
    print("Adding holiday calendar...")
    add_calendar_dates(OUTPUT_FILE)
    refresh_calendar(OUTPUT_FILE)
    generate_feed_info(OUTPUT_FILE)
    sort_stop_times(OUTPUT_FILE)
    print("Optimization complete")

    with open("latest_gtfs_key.txt", "w") as fh:
        fh.write(datetime.utcnow().strftime("%Y-%m-%d"))

    print("Done")


if __name__ == "__main__":
    main()
