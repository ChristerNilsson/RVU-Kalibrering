Innehåller pythonkod och dokumentation. Se wikin.

# rvu.csv

* `UENR` resans id
* `UEDAG` 1=mån .. 7=sön
* `D_A_S` start samsområde
* `D_B_S` mål samsområde
* `D_FORD` färdmedel *färdmedel.txt*
* `D_ARE` eller `D_AREALL` ärende *ärende.txt*
* `BOST_LAN` länsnummer *region.txt*
* `D_A_KL` start hhmm 0000 .. 2359
* `D_B_KL` mål hhmm 0000 .. 2359
* `D_A_SVE` 1=Sverige 2=annat land
* `D_B_SVE` 1=Sverige 2=annat land
* `D_A_PKT` typ av startplats *plats.txt*
* `D_B_PKT` typ av målplats *plats.txt*
* `VIKT_DAG` vikt

# aked.csv
* `UENR` se rvu.csv
* `D_A_S` se rvu.csv
* `D_B_S` se rvu.csv
* `purpose` *ärende.txt*
* `mode` *färdmedel.txt*
* `BOST_LAN` *region.txt*
* `region` *region.txt*
* `VIKT_DAG` se rvu.csv
* `tour` 1.. (ett UENR kan ha flera turer)
* `parts` 1=enkel 2=tur och retur

# bked.csv
Se aked.csv

# settings.json

Denna fil är personlig och ligger inte på github.

* `index`
	* Anger vilket projekt som ska köras. Namnen behöver inte vara heltal.
* `katalog`. Filnamnen är förutbestämda. Alla filer är kommaseparerade csv-filer (utf-8)
	* `rvu.csv` (IN)
	* `koder` (IN)
		* `arbete.txt`
		* `färdmedel.txt`
		* `plats.txt`
		* `region.txt`
		* `ärende.txt`
	* `aked.csv` (UT)
	* `bked.csv` (UT)
* `purpose`. Anger vilken kolumn som ska användas.
	* `D_ARE`
	* `D_AREALL`
* `options`
	* `A` = skapa `aked.csv`, dvs arbetsplatsbaserade resor
	* `B` = skapa `bked.csv`, dvs bostadsbaserade resor
	* `1` = resor med `parts` = 1 (enkelresor)
	* `2` = resor med `parts` = 2 (tur och retur)

* `A`: Lista över arbetsplatser
	* [4,5] *plats.txt*
* `B`: Lista med bostadsplatser
	* [1,2,3] *plats.txt*
```
{
    "0": {"katalog":"C:/github/RVU-kalibrering/SAMM_121400_414/",
        "options":"AB12", "purpose":"D_ARE", "A": [4,5], "B": [1,2,3]},
    "1": {"katalog":"C:/github/RVU-kalibrering/Syd_Skane-sundet_100_13/",
        "options":"AB12", "purpose":"D_ARE", "A": [],    "B": [1]},
    "2": {"katalog":"C:/github/RVU-kalibrering/SAMM_121400_15/",
        "options":"AB12", "purpose":"D_ARE", "A": [4,5], "B": [1,2,3]},
    "index" : "2"
}
```

