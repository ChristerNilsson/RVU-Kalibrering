Innehåller pythonkod och dokumentation. Se wikin.

# settings.json

Denna fil är personlig och ligger inte på github.

* index
	* Anger vilket projekt som ska köras. Namnen behöver inte vara heltal.
* katalog. Filnamnen är förutbestämda. Alla filer är kommaseparerade csv-filer (utf-8)
	* rvu.csv (IN)
	* koder (IN)
		* arbete.txt
		* färdmedel.txt
		* plats.txt
		* region.txt
		* ärende.txt
	* aked.csv (UT)
	* bked.csv (UT)
* purpose. Anger vilken kolumn som ska användas.
	* D_ARE
	* D_AREALL
* options
	* A = skapa aked.csv, dvs arbetsplatsbaserade resor
	* B = skapa bked.csv, dvs bostadsbaserade resor
	* 1 = resor med parts = 1 (enkelresor)
	* 2 = resor med parts = 2 (tur och retur)
```
{
    "0": {"options":"AB12", "katalog":"C:/github/RVU-kalibrering/SAMM_121400_414/",         "purpose":"D_ARE"},
    "1": {"options":"AB12", "katalog":"C:/github/RVU-kalibrering/Syd_Skane-sundet_100_13/", "purpose":"D_ARE"},
    "2": {"options":"AB12", "katalog":"C:/github/RVU-kalibrering/SAMM_121400_15/",          "purpose":"D_ARE"},
    "index" : "2"
}
```

