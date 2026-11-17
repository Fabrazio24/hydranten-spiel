"""Lädt Stadtgrenze, Ortsteile, Hydranten und Gebäude der Hansestadt Uelzen aus OpenStreetMap
(Overpass API) und schreibt sie kompakt nach data/uelzen.json. Läuft per GitHub Action."""
import json, os, sys, time, urllib.parse, urllib.request

ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]
UA = "hydranten-spiel-datenabruf/1.0"

def overpass(q):
    last = None
    for attempt in range(3):
        for url in ENDPOINTS:
            try:
                req = urllib.request.Request(url, data=urllib.parse.urlencode({"data": q}).encode(), headers={"User-Agent": UA})
                with urllib.request.urlopen(req, timeout=300) as r:
                    return json.load(r)
            except Exception as e:  # noqa
                last = e
                print("Fehler bei", url, e, file=sys.stderr)
        time.sleep(20)
    raise SystemExit(f"Overpass nicht erreichbar: {last}")

R = lambda v: round(v, 6)
AREA = '''rel["boundary"="administrative"]["admin_level"="8"]["name"~"Uelzen"](52.85,10.40,53.08,10.72)->.u;
.u map_to_area->.ua;'''

def lines_of(rel):
    return [[[R(p["lat"]), R(p["lon"])] for p in m["geometry"]]
            for m in rel.get("members", []) if m.get("type") == "way" and m.get("geometry") and m.get("role") in ("outer", "inner", "")]

def main():
    j = overpass(f'''[out:json][timeout:240];
{AREA}
.u out geom;
rel(area.ua)["boundary"="administrative"]["admin_level"~"^(9|10|11)$"];
out geom;
node(area.ua)["place"~"^(suburb|quarter|village|hamlet|neighbourhood)$"]["name"];
out;''')
    city = next(e for e in j["elements"] if e["type"] == "relation" and e.get("tags", {}).get("admin_level") == "8")
    city_lines = lines_of(city)
    lats = [p[0] for l in city_lines for p in l]; lons = [p[1] for l in city_lines for p in l]
    bbox = [min(lats), min(lons), max(lats), max(lons)]
    rels = [{"id": e["id"], "name": e["tags"]["name"], "lines": lines_of(e)}
            for e in j["elements"] if e["type"] == "relation" and e["id"] != city["id"] and e.get("tags", {}).get("name")]
    places = [{"id": e["id"], "name": e["tags"]["name"], "place": e["tags"]["place"], "pos": [R(e["lat"]), R(e["lon"])]}
              for e in j["elements"] if e["type"] == "node"]

    pad = 0.01
    bb = f"{bbox[0]-pad},{bbox[1]-pad*1.6},{bbox[2]+pad},{bbox[3]+pad*1.6}"
    h = overpass(f'[out:json][timeout:180];node["emergency"="fire_hydrant"]({bb});out;')
    hydrants = [[R(e["lat"]), R(e["lon"]), e.get("tags", {}).get("fire_hydrant:type", ""),
                 e.get("tags", {}).get("fire_hydrant:diameter", e.get("tags", {}).get("diameter", ""))]
                for e in h["elements"] if e["type"] == "node"]

    b = overpass(f'''[out:json][timeout:240];
{AREA}
way["building"](area.ua);
out tags geom;''')
    skip = {"roof", "carport", "ruins", "construction", "no", "transformer_tower", "tank", "silo", "bunker", "digester", "toilets", "kiosk"}
    buildings = []
    for e in b["elements"]:
        t = e.get("tags", {})
        g = e.get("geometry") or []
        if e["type"] != "way" or len(g) < 3 or t.get("building") in skip:
            continue
        poly = [[round(p["lat"], 5), round(p["lon"], 5)] for p in g]
        buildings.append({"t": t.get("building", "yes"), "n": t.get("name", ""),
                          "s": t.get("addr:street", ""), "h": t.get("addr:housenumber", ""), "p": poly})

    out = {"generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "source": "© OpenStreetMap-Mitwirkende (ODbL)",
           "city": {"id": city["id"], "name": city["tags"].get("name"), "lines": city_lines, "bbox": bbox},
           "ortsteile": rels, "places": places, "hydrants": hydrants, "buildings": buildings}
    os.makedirs("data", exist_ok=True)
    with open("data/uelzen.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(rels)} Ortsteil-Grenzen, {len(places)} Orte, {len(hydrants)} Hydranten, {len(buildings)} Gebäude")
    if len(hydrants) < 5:
        raise SystemExit("Zu wenige Hydranten gefunden")

main()
