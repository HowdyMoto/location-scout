# Scout prototype

Buildless web app in `dist/`. Serve locally with `python -m http.server 5281 --directory dist` from this folder.

Live: USGS earthquakes (past 24h), Seattle Fire dispatch (past 3h), Washington NWS alerts with geometry. Auto-refresh every 60 seconds. Failed feeds retain clearly marked last-known data. Aircraft, vessels, transit, and outages are explicitly fictional demo markers and can be disabled together. No credentials required.

Uses Leaflet 1.9.4, OpenStreetMap tiles, Google Fonts and Open-Meteo city search. External availability and CORS apply. No backend, tracking, or secrets. Saved views use localStorage. Not an emergency notification system.
