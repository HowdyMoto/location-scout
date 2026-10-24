# Location Scout

An interactive map prototype for exploring live public data in one place.

## Run locally

Requires Python 3. From the repository root:

```sh
python -m http.server 5281 --bind 127.0.0.1 --directory scout/dist
```

Open http://localhost:5281. On Windows, you can also run `scout/start.cmd`.

## Features

- Live USGS earthquakes from the past 24 hours
- Seattle Fire Department dispatches from the past 3 hours
- Washington National Weather Service alerts with geographic geometry
- Clearly labeled simulated aircraft, vessels, transit, and power outages
- Layer filters, city and coordinate search, saved views, and source details
- Automatic refresh every 60 seconds with visible feed availability

Aircraft, vessels, transit, and outage markers are fictional examples, not live tracking. Disable the demo toggle to see only public observations. Dispatches are published records, not confirmation of an ongoing emergency. This prototype is not an emergency notification system.

## Implementation

Buildless HTML, CSS, and JavaScript in `scout/dist/`, using Leaflet 1.9.4 and OpenStreetMap tiles. City search uses Open-Meteo; fonts use Google Fonts. External services require an internet connection and are subject to their own availability and usage terms. No API keys or backend are required. Saved views stay in browser localStorage.

JavaScript syntax check:

```sh
node --check scout/dist/app.js
```
