# GTFS Medellín

Automated pipeline for downloading, validating, improving, and publishing GTFS data for the Medellín metropolitan area.

This project downloads the official GTFS feed published by Metro de Medellín, applies automated improvements, validates the feed using MobilityData GTFS Validator, and publishes the resulting feed as GitHub Releases.

## Features

### Automated Download

The pipeline automatically downloads the latest GTFS feed from Metro de Medellín.

### Feed Normalization

Some releases contain GTFS files inside a nested directory. The pipeline automatically:

- Extracts the ZIP file
- Flattens nested folders
- Rebuilds the GTFS archive

This ensures all GTFS files are stored at the root of the archive as required by downstream tools.

### Calendar Maintenance

The pipeline automatically updates:

#### calendar.txt

Service dates are refreshed to cover:

- Current year
- Following year

#### calendar_dates.txt

Holiday exceptions are generated automatically using the Python `holidays` library for Colombia.

This includes:

- National holidays
- Semana Santa
- Ley Emiliani Monday holidays
- Fixed-date holidays

The generated exceptions automatically:

- Remove weekday service (`Laboral`) on holidays
- Remove Saturday service (`Sabado`) when a holiday occurs on Saturday
- Add holiday service (`Domingo-Festivo`)

No manual holiday maintenance is required.
