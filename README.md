# Travel Site Generator

A static site generator for creating interactive travel journals with maps, timelines, and statistics.

## Features

- **Interactive Maps**: Visualize your travel routes on a map with color-coded journeys
- **Timeline View**: Chronological display of all your trips and journeys
- **Statistics**: Automatic calculation of travel statistics including distances and modes of transport
- **Markdown Support**: Write trip descriptions in Markdown format
- **Multiple Transport Modes**: Support for plane, train, car, bus, ferry, bicycle, foot, metro, tram, and motorcycle

## Installation

### Prerequisites

- Python 3.14 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Install from source

```shell
$ git clone https://github.com/thomasleese/travel-site-generator.git
$ cd travel-site-generator
$ uv sync
```

## Usage

### 1. Set up your site structure

Create a directory with the following structure:

```
my-travel-site/
├── places.yaml
└── trips/
    └── my-trip.md
```

### 2. Define your places

In `places.yaml`, define all the locations you’ll reference in your trips using OpenStreetMap identifiers:

```yaml
Luton-Airport: W110273499
Paris-CDG: W294032205
Paris-Montparnasse: W11865818
Toulouse-Matabiau: W11871819
Rodez-Gare: W12591817
Camares: W12591817
Toulouse-Blagnac: W11865820
```

You can find OpenStreetMap IDs by searching for locations on [OpenStreetMap](https://www.openstreetmap.org) or [Nominatim](https://nominatim.openstreetmap.org).

### 3. Create your trip files

In the `trips` directory, create Markdown files with journey information in the front matter. Use `===` to delimit the front matter from the content:

```markdown
===
From Luton-Airport on 2018-07-03
To Paris-CDG by plane

From Paris-Montparnasse on 2018-07-06
To Toulouse-Matabiau by train
To Rodez-Gare

From Camares on 2018-07-11
To Toulouse-Blagnac by car
To Luton-Airport by train
===

# My Trip to France

This was an amazing trip where I visited Paris and the French countryside.
```

#### Journey Syntax

Each journey consists of one or more legs. A leg requires:

- **From**: The origin place
- **On**: The date (YYYY-MM-DD format)
- **To**: The destination place
- **By**: The mode of transport (optional, defaults to previous leg’s mode)

Example variations:

```
From heathrow on 2020-01-01 to gatwick by plane
From heathrow on 2020-01-01
To gatwick by plane
From heathrow to gatwick on 2020-01-01 by plane
```

Multi-leg journeys (connected legs with the same date):

```
From heathrow on 2020-01-01 to gatwick by plane
To stansted by train
```

#### Supported Modes of Transport

- `bicycle`
- `bus`
- `car`
- `ferry`
- `foot`
- `metro`
- `motorcycle`
- `plane`
- `train`
- `tram`

### 4. Generate your site

Run the generator from your site directory:

```shell
$ travel-site-generator
```

This will create a `site` directory with:
- `index.html` - The main page with map, timeline, and statistics
- `data.json` - GeoJSON data for the map
- `static/` - CSS styles and other static assets

#### Command Line Options

```shell
# Specify custom input directory (default: current directory)
$ travel-site-generator --input /path/to/your/site

# Specify custom output directory (default: ./site)
$ travel-site-generator --output /path/to/output

# Provide Google Maps API key for route calculation
$ travel-site-generator --gmaps-api-key YOUR_API_KEY
```

### 5. View your site

Open `site/index.html` in your browser, or serve it with a local server:

```shell
$ cd site
$ python -m http.server 8000
```

Then visit `http://localhost:8000` in your browser.

## Development

### Setting up the development environment

```shell
$ uv sync --all-extras --dev
```

### Running tests

Tests are written using pytest and are located in the `tests` directory.

```shell
$ uv run pytest
```

### Linting

The project uses [Ruff](https://github.com/astral-sh/ruff) for linting.

```shell
$ uv run ruff format
$ uv run ruff check
```

## License

[MIT Licence](LICENCE.md)
