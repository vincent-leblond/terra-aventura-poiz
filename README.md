# terra-aventura-poiz

Analyse des poï'z de Terra Aventura

## Configuration

1. Installer Python
2. Installer les librairies données dans *requirements.txt* : ```pip3 install -r requirements.txt```

## Trouver les Poï'z à proximité des gares ferroviaires (moins de 1,5 km)

Exécuter le script *src/analysis.py*

```bash
cd src
python3 analysis.py
```

Le résultat est donné dans *data/outputs/geotable.geojson*