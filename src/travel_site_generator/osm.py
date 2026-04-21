import httpx


class Nominatim:
    def lookup(self, *, osm_ids):
        url = "https://nominatim.openstreetmap.org/lookup"
        params = {"osm_ids": ", ".join(osm_ids), "format": "jsonv2"}
        headers = {"User-Agent": "travel-journal-generator", "Accept-Language": "en"}
        response = httpx.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
