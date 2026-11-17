# Finde den Hydranten

Browser-Minispiel für die Hansestadt Uelzen: Fünf zufällige Brandobjekte, für jedes setzt du einen Pin dort, wo du den nächsten Hydranten vermutest. Die Abweichung zum echten Hydranten (laut OpenStreetMap) bestimmt die Punkte.

**Spielen:** https://fabrazio24.github.io/hydranten-spiel/

- Gebiet wählbar: Hansestadt Uelzen gesamt, einzelne Ortsteile oder eigener Kartenausschnitt
- Daten: OpenStreetMap über die Overpass API (`emergency=fire_hydrant`), live im Browser geladen
- Punkte: 5.000 bis 5 m Abweichung, danach abnehmend (100 m ≈ 1.750)

Alles steckt in `index.html` (Leaflet 1.9.4 eingebettet).
