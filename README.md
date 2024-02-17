# http-schemas.nav.gov.hu-2013-szamla-kerekito
Összesítés kerekítő olyan könyvelő programokhoz amik nem fogadnak el forintfillért (pl Infotéka)

Kerekít minden számot (bruttó+nettó+áfa) az összesítés szekcióban (végösszeg+áfarovat) minden számlán egy http://schemas.nav.gov.hu/2013/szamla típusú xml fájlban. A kerekítés szabványos módon megy végbe "\*,50" alatt lefelé, "\*,50" és afelett felfelé kerekítve.

Ha a nettó+áfa nem egyenlő a bruttóval bármelyik rovatban akkor javítja a nettót (lehet konfigurálni hogy inkább az áfát).

__Javítás ahhoz amikor a részösszegek összege nem egyezik a végösszeggel nincs megírva, ilyenkor a program kilép és nem menti a javított fájlt!__

## Kovetelmenyek

* Legyen feltelepítve [Python](https://www.python.org/downloads/) 3.8+
* Legyen lementve [rounder.py](https://github.com/Gr3q/http-schemas.nav.gov.hu-2013-szamla-kerekito/raw/main/rounder.py) (jobb klikk+mentés másként)

## Használat

Futtasd igy a terminalbol:

```bash
python rounder.py {{fajl}}
```

ahol a fájl amin futtatni akarod.

_Tipp: Windowsban ha beírod a Windows Explorer fájl sávjaba hogy "cmd" es lenyomod az Entert akkor felhozza a terminált abban a mappában ami meg volt nyitva._

A teljes segítség

```bash
python rounder.py --help
usage: rounder.py [-h] [--out_folder OUT_FOLDER] [--force | --no-force] [--overwrite | --no-overwrite] [--correct {netto,afa}] input

Kerekít minden számot (bruttó+nettó+áfa) az összesítés szekcióban (végösszeg+áfarovat) minden számlán egy "http://schemas.nav.gov.hu/2013/szamla" típusú xml fájlban. A kerekítés szabványos módon megy végbe "*,50" alatt lefelé, "*,50" és afelett felfelé kerekítve.

positional arguments:
  input                 Az input xml fájl

options:
  -h, --help            show this help message and exit
  --out_folder OUT_FOLDER
                        Az output xml mappa. Alapértermezett érték az input fájl mappája.
  --force, --no-force   Akkor is megpróbál kerekíteni ah ay inut fájl nem felel meg a várt formátumnak. Alapértelmezett érték: False.
  --overwrite, --no-overwrite
                        Felülírja az output fájlt, ha már létezik. Alapértelmezett érték: False.
  --correct {netto,afa}
                        Kijavítja a az egyik részösszeget, ha nem egyezik a bruttó összegével. Alapértelmezett érték: netto.
```
