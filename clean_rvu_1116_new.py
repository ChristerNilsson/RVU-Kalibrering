# Process för att läsa in och rensa delresor
# Inläsning av data

import pandas as pd
import json
import math
import numpy as np

UNKNOWN = -99

def runAsserts():

	assert ConvertToMinutes(99) == 99
	assert ConvertToMinutes(UNKNOWN) == UNKNOWN
	assert ConvertToMinutes(100) == 60
	assert ConvertToMinutes(130) == 90
	assert ConvertToMinutes(2400) == UNKNOWN

	rows = [{'A':1}, {'A':1}, {'A':2}]
	assert groupBy(rows,['A']) == {'1':[{'A':1},{'A':1}], '2':[{'A':2}]}

	assert ModeHierarchy(['buss','spv','cykel']), 'koll'
	assert ModeHierarchy(['gång','gång','cykel']), 'cykel'
	assert ModeHierarchy(['ånglok','sparkcykel']), 'övrigt'

	assert ModeRecoded('gång') == 'gång'
	assert ModeRecoded('buss') == 'koll'
	assert ModeRecoded('sparkcykel') == 'övrigt'

	rows = [{'A':1, 'B':2, 'C':3}, {'A':4, 'B':5, 'C':6}]
	assert pickColumns(['A','C'],rows) == [{'A':1, 'C':3}, {'A':4, 'C':6}]
	assert renameColumns({'A':'Adam','C':'Cesar'},rows) == [{'Adam':1, 'B':2, 'Cesar':3}, {'Adam':4, 'B':5, 'Cesar':6}]

	assert mode_lookup[1] == 'gång'
	assert mode_lookup[2] == 'cykel'

	assert purpose_lookup[2] == 'Arbete'
	assert purpose_lookup[3] == 'Skola'

	assert place_lookup[2] == 'bostad_ovr'
	assert place_lookup[3] == 'bostad_fri'

	assert region_lookup[1] == 'SAMM'
	assert region_lookup[14] == 'Väst'

	assert work_lookup[3] == 'arbetar'
	assert work_lookup[4] == 'övrigt'

def ConvertToMinutes(t):
	if t >= 2400 or t == UNKNOWN: return UNKNOWN
	hour = t // 100
	minute = t % 100
	return 60 * hour + minute

def CreateDiary(trip_list):
	## ToDo: Identify work based tours

	if len(trip_list) == 0: return []

	idx = 1
	tour = 1
	day_type = trip_list[0]['a_p'] + '->' + trip_list[-1]['b_p']

	# First, create a morning activity, wherever the person starts their morning (usually at home, sometimes somewhere else)
	at_home_morning = {
		'zoneA': trip_list[0]['A_SAMS'],
		'zoneB': trip_list[0]['B_SAMS'],
		'mode': 'aktivitet',
		'purpose': trip_list[0]['a_p'],
		'tour': tour,
		'act': idx,
		'day_type': day_type,
		'a_kl': trip_list[0]['a_kl'],
		'b_kl': trip_list[0]['b_kl'],
		'end_tour': '',
		'DAG': trip_list[0]['DAG'],
		'weight': trip_list[0]['VIKT'],
		'UENR': trip_list[0]['UENR'],
	}

	activities = []
	activities.append(at_home_morning)
	for row in trip_list:
		trip_start = row['a_kl']
		trip_end = row['b_kl']
		act_start = trip_end
		activities[idx - 1]['b_kl'] = trip_start

		# Identify trips that end up at home
		purpose = row['purpose']
		end_tour = False
		if row['b_p'] == 'bostad':
			purpose = 'bostad'
			end_tour = True

		# Add the trip to the diary
		trip = {
			'zoneA': row['A_SAMS'],
			'zoneB': row['B_SAMS'],
			'mode': row['mode'],
			'purpose': purpose,
			'tour': tour,
			'act': idx + 1,
			'day_type': day_type,
			'a_kl': trip_start,
			'b_kl': trip_end,
			'end_tour' : end_tour,
			'DAG': row['DAG'],
			'weight': row['VIKT'],
			'UENR': row['UENR'],
		}
		activities.append(trip)
		idx += 1

		# Add the next activity to the diary
		act = {
			'zoneA': row['A_SAMS'],
			'zoneB': row['B_SAMS'],
			'mode': 'aktivitet',
			'purpose': purpose,
			'tour': tour,
			'act': idx + 1,
			'day_type': day_type,
			'a_kl': act_start,
			'b_kl': act_start,
			'end_tour' : end_tour,
			'DAG': row['DAG'],
			'weight': row['VIKT'],
			'UENR': row['UENR'],
		}
		activities.append(act)
		idx += 1

		if end_tour:
			tour += 1

	for row in activities:
		row['dur'] = ConvertToMinutes(row['b_kl']) - ConvertToMinutes(row['a_kl'])
	return activities

def groupBy(arr, cols):
	result = {}
	for row in arr:
		value = [str(row[col]) for col in cols]
		value = ':'.join(value)
		if value not in result:
			result[value] = [row]
		else:
			result[value].append(row)
	return result

def ModeHierarchy(modes):
	""" Färdmedelshierarki enl Staffan Algers modifierat så att tåg ingår i koll indata: en lista av alla fm under resan utdata: huvudfm """
	if 'tåg' in modes: return 'koll'
	elif 'tbana' in modes: return 'koll'
	elif 'spv' in modes: return 'koll'
	elif 'buss' in modes: return 'koll'
	elif 'bil' in modes: return 'bil'
	elif 'pass' in modes: return 'pass'
	elif 'cykel' in modes: return 'cykel'
	elif 'gång' in modes: return 'gång'
	else: return 'övrigt'

def ModeRecoded(mode):
	"""Kodar om tåg, tbana etc till koll"""
	if mode == 'tåg': return 'koll'
	elif mode == 'tbana': return 'koll'
	elif mode == 'spv': return 'koll'
	elif mode == 'buss': return 'koll'
	elif mode == 'bil': return 'bil'
	elif mode == 'pass': return 'pass'
	elif mode == 'cykel': return 'cykel'
	elif mode == 'gång': return 'gång'
	else: return 'övrigt'

def pickColumns(cols, rows):
	result = []
	for r in rows:
		obj = {}
		for col in cols:
			obj[col] = r[col]
		result.append(obj)
	return result

def renameColumns(trans, rows):
	for r in rows:
		for col in trans:
			r[trans[col]] = r[col]
			del r[col]
	return rows

def replaceNA(rvu):
	for row in rvu:
		for key in row:
			if key == 'VIKT':
				row[key] = round(row[key], 3)
			else:
				row[key] = UNKNOWN if math.isnan(row[key]) else round(row[key])
	return rvu

def TourProperties(tour_diary):
	all_activities = [r for r in tour_diary if r['mode'] == 'aktivitet']
	activities = [r for r in all_activities if r['purpose'] != 'bostad']
	trips = [r for r in tour_diary if r['mode'] != 'aktivitet']

	uenr = trips[0]['UENR']
	dag = trips[0]['DAG']
	weight = trips[0]['weight']

	tour = trips[0]['tour']
	zoneA = trips[0]['zoneA']
	zoneB = trips[0]['zoneB']

	result = [trip['mode'] for trip in trips]
	mode = ModeHierarchy(result)

	for trip in trips:
		trip['mode'] = ModeRecoded(trip['mode'])

	mainmode_trips = [r for r in trips if r['mode'] == mode]
	main_zone = [t for t in tour_diary if t['purpose'] != 'bostad']

	if len(main_zone) != 0:
		zone = max(main_zone, key=lambda item: item['dur'])
	else:
		zone = max(tour_diary, key=lambda item: item['dur'])
	zoneB = zone['zoneB']

	# Turer som inte har någon aktivitet definieras som rundturer.
	if len(activities) == 0:
		dur = sum([trip['dur'] for trip in trips])
		return {
			'zoneA': trips[0]['zoneA'],
			'zoneB': trips[0]['zoneB'],
			'mode': mode,
			'purpose': trips[0]['purpose'] + '_rundtur',
			'DAG': dag,
			'tour': tour,
			'weight': weight,
			'Adur': dur,
			'Mdur': dur,
			'parts': 2,
			'UENR': uenr,
			'split_act': False,
		}

	# Annars är det en tur med ett ärende
	else:
		actList = [activity['purpose'] for activity in activities]
		if 'Arbete' in actList:  # Ifall det finns ett arbete-ärende i turen sätts ärendet till det
			purpose = 'Arbete'
			zoneB = [a for a in activities if a['purpose'] == 'Arbete'][0]['zoneB']
		elif 'Tjänste' in actList:  # Ifall det finns ett tjänste-ärende i turen sätts ärendet till det
			purpose = 'Tjänste'
			zoneB = [a for a in activities if a['purpose'] == 'Tjänste'][0]['zoneB']
		else:  # Annars välj den längsta aktiviteten som ärende
			main_activity = max(activities, key=lambda item: item['dur'])
			purpose = main_activity['purpose']
		# När vi bestämt huvudärende så använder vi alla de aktiviteterna
		acts = [act for act in activities if act['purpose'] == purpose]
		Adur = sum([act['dur'] for act in acts])
		Mdur = sum([trip['dur'] for trip in mainmode_trips])
		split_act = len(acts) > 1

		parts = 2 if tour_diary[-1]['end_tour'] else 1

		return {
			'zoneA': zoneA,
			'zoneB': zoneB,
			'mode': mode,
			'purpose': purpose,
			'DAG': dag,
			'tour': tour,
			'weight': weight,
			'Adur': Adur,
			'Mdur': Mdur,
			'parts' : parts,
			'UENR': uenr,
			'split_act': split_act,
		}

with open('settings.json') as f: settings = json.load(f)
root = settings['root']
input = root + settings['input']
output = root + settings['output']
rvu_input = input + settings['rvu']
tour_arb_output = output + "tour_arb.csv"
koder = root + settings['koder']
skiprows = settings['skiprows']
nrows = settings['nrows']

dtype = {'id': np.int32}
mode_codes = pd.read_csv(koder + "fm_kod.txt", sep='\t', dtype = dtype )
mode_lookup = dict(zip(mode_codes["id"], mode_codes["grp"]))

purpose_codes = pd.read_csv(koder + "ärende_kod_gen.txt", sep='\t')
purpose_lookup = dict(zip(purpose_codes["id"], purpose_codes["grp"]))

place_codes = pd.read_csv(koder + "plats_kod.txt", sep='\t')
place_lookup = dict(zip(place_codes["id"], place_codes["plats"]))

region_codes = pd.read_csv(koder + "region_kod.txt", sep=',')
region_lookup = dict(zip(region_codes["lkod"], region_codes["region"]))

work_codes = pd.read_csv(koder + "arbete_kod.txt", sep='\t')
work_lookup = dict(zip(work_codes["kod"], work_codes["status"]))

runAsserts()

cols = "Lopnr,UENR,AR,Manad,DAG,HNR,DNR,BOSAMS,S_KL,SP,S_SAMS,SV1,M_KL,MP,M_SAMS,SV2,HAR,DAR,FRD,KM,TID,H_ANT,H_ANT_DR,H_BARNN,H_BARNV,H_ENKEL,H_ENSAM,H_FORDON,H_PERS,D_PERS,FRD_agg,HAR_agg,DAR_agg,ID,Zon_a,Zon_b,KORKORT,Vikt,Noll,SP1_MP1".split(',')

#cols = "UENR,BOST_LAN,D_ARE,D_FORD,D_A_KL,D_B_KL,UEDAG,VIKT_DAG,D_A_S,D_B_S,D_A_SVE,D_B_SVE,D_A_PKT,D_B_PKT".split(',')
#cols = "UENR,HAR,FRD,S_KL,M_KL,DAG,Vikt,BOSAMS,S_SAMS,M_SAMS,SV1,SV2,SP,MP,HAR_agg".split(',')
rvuA = pd.read_csv(rvu_input, usecols=cols, nrows=nrows, skiprows=range(1,skiprows))
rvuB = rvuA.to_dict('records')
rvuB = replaceNA(rvuB)

# Koda om färdmedel, ärende etc
# Vi kodar om resvaneundersökningens sifferkoder för till exempel färdmedel till de grupperade färdmedel som används i Sampers. Detsamma görs för ärende, plats (dvs bostad, arbetsplats, skola, annat). Vi kodar också på Sampers-region istället för län så att vi kan titta på eventuella skillnader mellan regionerna senare.
# I RVU:erna är skola ett ärende, medan Sampers skiljer på skola för olika åldersgrupper. Här använder vi samma uppdelning som i skattningen, dvs i tre grupper: Grundskola för åldrarna 6-15 år, gymnasium för 16-18 år och vuxenutbildning för 19 år och uppåt.
# Read and define lookup tables for survey codes

rvuC = [r for r in rvuB if r['SV1'] == 1 and r['SV2'] == 1] # filtera bort utrikesresor

#cols = 'UENR,UEDAG,VIKT_DAG,D_A_S,D_B_S,D_FORD,D_ARE,D_A_PKT,D_B_PKT,D_A_KL,D_B_KL,BOST_LAN'.split(',')
#rvuD = pickColumns(cols, rvuC)
rvuE = renameColumns({"S_KL":"A_KL", "M_KL":"B_KL", "SP":"A_P", "MP":"B_P", "S_SAMS":"A_SAMS", "M_SAMS":"B_SAMS", "Vikt":"VIKT"}, rvuC) # "DAG": "DAG", "FRD":"FRD",
rvuF = [r for r in rvuE if r['DAG'] <= 7] # filtrera fram veckodagar.
rvuG = [r for r in rvuF if not (r['A_P'] == 1 and r['B_P'] == 1 or r['A_P'] == 2 and r['B_P'] == 2 or r['A_P'] == 3 and r['B_P'] == 3)] # filtrera bort rundresor

for row in rvuG:
	#print(row['UENR'])
	row['mode'] = mode_lookup[row['FRD']]

	#row["purpose"] = row["HAR"] #purpose_lookup[row["ARE"]]
	row["purpose"] = row["HAR_agg"] #purpose_lookup[row["ARE"]]
	#row["purpose"] = purpose_lookup[row["ARE"]]

	row["a_p"] = place_lookup[row["A_P"]]
	row["b_p"] = place_lookup[row["B_P"]]
	row['a_kl'] = row["A_KL"]
	row['b_kl'] = row["B_KL"]
	row['LAN'] = row['BOSAMS']//1000000
	if row["LAN"] == -1:
		row["region"] = -1
	else:
		row["region"] = region_lookup[row["LAN"]]

rvuH = groupBy(rvuG, ['UENR'])

# Skapa resedagbok av delresor
# Vi börjar med att gruppera delresorna per individ. För varje grupp körs funktionen `CreateDiary` som är definierad i filen `create_diary.py`. I den funktionen läggs det in aktiviteter före, mellan och efter delresorna så att hela dagen är fylld av antingen resor eller aktiviteter. Först läggs en hemma-, arbete- eller övrigt-aktivitet till i början, beroende på var individien startar sin dag. Vi noterar den informationen i utdata för att senare kommer vi att sortera bort resor som inte startat och slutat hemma. För varje resa läggs sedan en aktivitet till efter resan som börjar när resan slutar. Ärendet definieras av det ärende som uppgetts för resan. Sluttiden sätts till starttiden för nästa resa. Den sista aktiviteten får sluttid 23.59 utom i de fall då resandet pågår till efter midnatt. Då sätts den sista aktiviteten till en minut efter start.
# Vi kommer senare att använda den här utökade listan av resor och aktiviteter för att kunna se när olika aktiviteter utförs och för att kunna definiera huvudresans ärende efter vilken aktivitet som är längst i de fall det inte finns någon arbetsresa eller tjänsteresa.

rvuI = []
for group in rvuH:
	lst = CreateDiary(rvuH[group])
	for item in lst:
		rvuI.append(item)

rvuJ = [r for r in rvuI if r['day_type'] in ['bostad->bostad','bostad->annat','bostad->bostad_ovr','bostad->bostad_fri']]  # homebased_diaries
rvuK = groupBy(rvuJ, ['UENR', 'tour'])
rvuL = [TourProperties(rvuK[group]) for group in rvuK]

cols = 'UENR,DAG,tour,purpose,mode,weight,Adur,Mdur,zoneA,zoneB,parts'.split(',')
rvuM = pickColumns(cols, rvuL)

if len(rvuM) > 0:
	ttdf_arb = pd.DataFrame.from_dict(rvuM)
	ttdf_arb.to_csv(tour_arb_output, index=False, columns=cols)
