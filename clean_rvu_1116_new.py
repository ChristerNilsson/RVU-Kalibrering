# Process för att läsa in och rensa delresor
# Inläsning av data

import pandas as pd
import json
import math
import numpy as np
import pydash as _
import operator

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
	#assert pickColumns(['A','C'],rows) == [{'A':1, 'C':3}, {'A':4, 'C':6}]
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

def freq (arr):
	d = {}
	for item in arr:
		if item not in d: d[item] = 0
		d[item] += 1
	return d

def ToTimestep(minutes): return minutes // 30 # Gör om tid-från-midnatt till tidsperiod

def RangeFromStartEnd(start, end):
  ranges = []
  s = ToTimestep(start)
  e = 1 + ToTimestep(end)
  if e <= s:
    # Special case when activity crosses midnight
    e_m = 1 + ToTimestep(24 * 60 - 1)
    s_m = ToTimestep(24*60)
    ranges.append(range(s, e_m))
    ranges.append(range(s_m, e))
  else:
    ranges.append(range(s,e))
  return ranges

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
			if key == 'VIKT_DAG':
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

def WB_TourProperties(tour_diary):
	all_activities = [r for r in tour_diary if r['mode'] == 'aktivitet']
	activities = [r for r in all_activities if r['purpose'] != 'bostad']
	trips = [r for r in tour_diary if r['mode'] != 'aktivitet']

	uenr = trips[0]['UENR']
	tour_id = trips[0]['tour']
	dag = trips[0]['DAG']
	weight = trips[0]['weight']
	zoneA = trips[0]['zoneA']
	zoneB = trips[0]['zoneB']

	result = [trip['mode'] for trip in trips]
	mode = ModeHierarchy(result)

	for trip in trips:
		trip['mode'] = ModeRecoded(trip['mode'])

	mainmode_trips = [r for r in trips if r['mode'] == mode]

	# Kollar att turen har monotont stigande avresa/ankomst för alla resor
	# is_mono = tour_diary[['start_time', 'end_time']].apply(lambda x: x.is_monotonic_increasing, axis=0)
	# from_ok = is_mono['start_time']
	# to_ok = is_mono['end_time']
	# times_ok = from_ok and to_ok

	#lista = [tour['a_kl'] for tour in tour_diary]
	times_ok =              _.is_monotone([tour['a_kl'] for tour in tour_diary], operator.le)
	times_ok = times_ok and _.is_monotone([tour['b_kl'] for tour in tour_diary], operator.le)
	times_ok = True
	#is_monotone([1, 1, 2, 3], operator.le)

	reason = ""
	if not times_ok:
		print([tour['a_kl'] for tour in tour_diary])
		print([tour['b_kl'] for tour in tour_diary])
		reason = 'non-monotonic'

	roundtrip = len(activities) == 0
	if roundtrip:
		reason = 'roundtrip'

	work_trip = 'Arbete' in [activity['purpose'] for activity in activities]
	business_trip = 'Tjänste' in [activity['purpose'] for activity in activities]

	if ~(work_trip and business_trip):
		reason = 'non-WB-business'

	ok = times_ok and not roundtrip and work_trip and business_trip

	if not ok:
		# print(f'{uenr} not ok, from ok {from_ok}, to ok {to_ok}')
		# print(tour_diary)

		dur = sum([trip['dur'] for trip in trips])
		return {
			'UENR': uenr,
			'tour': tour_id,
			'DAG': dag,
			'zoneA': zoneA,
			'zoneB': zoneB,
			'purpose': reason,
			'mode': mode,
			'weight': weight,
			'Adur': dur,
			'Mdur': dur,
			'split_act': False,
			# 'activity_range': [],
			# 'trip_range': [],
			# 'main_trip_range': [],
			# 'outbound_range': [],
			# 'inbound_range': []
		}

	# Kandidat att ha en arbetsplatsbaserad tjänsteresa
	else:

		# act_range = RangeFromStartEnd(trips[0]['a_kl'], trips[-1]['b_kl'])
		# Vi vill veta om det finns flera 'Arbete'-aktiviteter
		work_acts = [a for a in activities if a['purpose'] == 'Arbete']
		split_act = len(work_acts) > 1

		# Om vi har en uppdelad arbets-aktivitet behöver vi kolla
		# om den har en tjänsteresa i mitten nånstans
		if split_act:

			# Plocka ut de resor och aktiviteter som är mitt i arbetsresan
			acts = [a for a in activities if a['purpose'] == 'Tjänste' and a['a_kl'] >= work_acts[0]['a_kl'] and a['b_kl'] <= work_acts[-1]['b_kl']]
			if len(acts) < 1:
				return {
					'UENR': uenr,
					'tour': tour_id,
					'DAG': dag,
					'zoneA': zoneA,
					'zoneB': zoneB,
					'purpose': reason,
					'mode': mode,
					'weight': weight,
					'Adur': 0,
					'Mdur': 0,
					'split_act': split_act,
					# 'activity_range': [],
					# 'trip_range': [],
					# 'main_trip_range': [],
					# 'outbound_range': [],
					# 'inbound_range': []
				}
			if len(trips) < 1:
				return {
					'UENR': uenr,
					'tour': tour_id,
					'DAG': dag,
					'zoneA': zoneA,
					'zoneB': zoneB,
					'purpose': 'non-WB-business',
					'mode': mode,
					'weight': weight,
					'Adur': 0,
					'Mdur': 0,
					'split_act': split_act,
					# 'activity_range': [],
					# 'trip_range': [],
					# 'main_trip_range': [],
					# 'outbound_range': [],
					# 'inbound_range': []
				}

			# filter_tripstart = trips['a_kl'] >= work_acts[0]['a_kl']
			# filter_tripend = trips['b_kl'] >= work_acts[-1]['b_kl']
			# wb_trips = [t for t in trips if t['a_kl'] >= work_acts[0]['a_kl'] and t['b_kl'] >= work_acts[-1]['b_kl']]

			#wb_mainmode = trips.loc[trips['duration'].idxmax()]['mode']
			wb_mainmode = max([trip for trip in trips], key=lambda r : r["dur"])["mode"]

			#wb_longest_act = acts.loc[acts['duration'].idxmax()]
			wb_longest_act = max([act for act in acts], key=lambda r : r["dur"])

			#main_zone = [t for t in tour_diary if t['purpose'] != 'bostad']
			#zone = max(main_zone, key=lambda r : r["dur"])

			act_duration = sum([a['dur'] for a in acts])
			mainmode_duration = sum([trip['dur'] for trip in trips if trip['mode'] == wb_mainmode])
			act_range = RangeFromStartEnd(wb_longest_act['a_kl'], wb_longest_act['b_kl'])

			if len(act_range) > 1:
				pass
				# s_act = act_range[0][0]
				# e_act = act_range[-1][-1]
			else:
				# if len(act_range[0]) > 1:
				# 	s_act = act_range[0][0]
				# 	e_act = act_range[0][-1]
				# elif isinstance(act_range[0], int):
				# 	s_act = act_range
				# 	e_act = s_act
				# else:
				# 	s_act = act_range[0][0]
				# 	e_act = s_act

				# outbound_range = []
				# inbound_range = []
				# trip_range = []
				# wp_range = []
				# for t in trips:
				# 	ranges = RangeFromStartEnd(t['a_kl'], t['b_kl'])
				# 	trip_range.extend(ranges)
				# main_trip_range = []
				# for mt in mainmode_trips:
				# 	ranges = RangeFromStartEnd(mt['a_kl'], mt['b_kl'])
				# 	main_trip_range.extend(ranges)
				# 	s = ranges[0][0]
				# 	if s <= s_act: outbound_range.extend(ranges)
				# 	if s >= e_act: inbound_range.extend(ranges)

				tour = {
					'UENR': uenr,
					'tour': tour_id,
					'DAG': dag,
					'zoneA': zoneA,
					'zoneB': zoneB,
					'purpose': 'Tjänste (AB)',
					'mode': mode,
					'weight': weight,
					'Adur': act_duration,
					'Mdur': mainmode_duration,
					'split_act': split_act,
					# 'activity_range': act_range,
					# 'trip_range': trip_range,
					# 'main_trip_range': main_trip_range,
					# 'outbound_range': outbound_range,
					# 'inbound_range': inbound_range

				}
		# Annars har den ingen arbetsplatsbaserad tur
		else:
			tour = {
				'UENR': uenr,
				'tour': tour_id,
				'DAG': dag,
				'zoneA': zoneA,
				'zoneB': zoneB,
				'purpose': 'non-WB-business',
				'mode': mode,
				'weight': weight,
				'Adur': 0,
				'Mdur': 0,
				'split_act': split_act,
				# 'activity_range': [],
				# 'trip_range': [],
				# 'main_trip_range': [],
				# 'outbound_range': [],
				# 'inbound_range': []
			}

	return tour

with open('settings.json') as f: settings = json.load(f)
root = settings['root']
input = root + settings['input']
output = root + settings['output']
rvu_input = input + settings['rvu']
tour_arb_output = output + "tour_arb.csv"
tour_WB_output = output + "tour_WB.csv"
koder = root + settings['koder']
skiprows = settings['skiprows']
nrows = settings['nrows']

dtype = {'id': np.int32}
mode_codes = pd.read_csv(koder + "fm_kod.txt", sep='\t', dtype = dtype )
mode_lookup = dict(zip(mode_codes["id"], mode_codes["grp"]))

purpose_codes = pd.read_csv(koder + "ärende_kod_gen.txt", sep='\t', dtype = dtype)
purpose_lookup = dict(zip(purpose_codes["id"], purpose_codes["grp"]))

place_codes = pd.read_csv(koder + "plats_kod.txt", sep='\t')
place_lookup = dict(zip(place_codes["id"], place_codes["plats"]))

region_codes = pd.read_csv(koder + "region_kod.txt", sep=',')
region_lookup = dict(zip(region_codes["lkod"], region_codes["region"]))

work_codes = pd.read_csv(koder + "arbete_kod.txt", sep='\t')
work_lookup = dict(zip(work_codes["kod"], work_codes["status"]))

runAsserts()

cols = "UENR,UEDAG,BOST_LAN,D_ARE,D_FORD,D_A_KL,D_B_KL,UEDAG,VIKT_DAG,D_A_S,D_B_S,D_A_SVE,D_B_SVE,D_A_PKT,D_B_PKT".split(',')
rvuA = pd.read_csv(rvu_input, usecols=cols, nrows=nrows, skiprows=range(1,skiprows))
rvuB = rvuA.to_dict('records')
rvuB = replaceNA(rvuB)

# Koda om färdmedel, ärende etc
# Vi kodar om resvaneundersökningens sifferkoder för till exempel färdmedel till de grupperade färdmedel som används i Sampers. Detsamma görs för ärende, plats (dvs bostad, arbetsplats, skola, annat). Vi kodar också på Sampers-region istället för län så att vi kan titta på eventuella skillnader mellan regionerna senare.
# I RVU:erna är skola ett ärende, medan Sampers skiljer på skola för olika åldersgrupper. Här använder vi samma uppdelning som i skattningen, dvs i tre grupper: Grundskola för åldrarna 6-15 år, gymnasium för 16-18 år och vuxenutbildning för 19 år och uppåt.
# Read and define lookup tables for survey codes

rvuC = [r for r in rvuB if r['D_A_SVE'] == 1 and r['D_A_SVE'] == 1] # filtera bort utrikesresor
rvuE = renameColumns({"D_A_KL":"A_KL", "D_B_KL":"B_KL", "D_A_PKT":"A_P", "D_B_PKT":"B_P", "D_ARE":"ARE", "D_FORD":"FRD", "BOST_LAN":"LAN", "UEDAG": "DAG", "D_A_S":"A_SAMS", "D_B_S":"B_SAMS","VIKT_DAG":"VIKT"}, rvuC)
rvuF = [r for r in rvuE if r['DAG'] <= 7] # filtrera fram veckodagar.
rvuG = [r for r in rvuF if not (r['A_P'] == 1 and r['B_P'] == 1 or r['A_P'] == 2 and r['B_P'] == 2 or r['A_P'] == 3 and r['B_P'] == 3)] # filtrera bort rundresor

for row in rvuG:
	row['mode'] = mode_lookup[row['FRD']]
	row["purpose"] = purpose_lookup[row["ARE"]]
	row["a_p"] = place_lookup[row["A_P"]]
	row["b_p"] = place_lookup[row["B_P"]]
	row['a_kl'] = row["A_KL"]
	row['b_kl'] = row["B_KL"]
	row['weight'] = row["VIKT"]
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

cols = 'UENR,DAG,tour,purpose,mode,weight,Adur,Mdur,zoneA,zoneB,parts'.split(',')
rvuJ = [r for r in rvuI if r['day_type'] in ['bostad->bostad','bostad->annat','bostad->bostad_ovr','bostad->bostad_fri']]  # homebased_diaries
rvuK = groupBy(rvuJ, ['UENR', 'tour'])
rvuL = [TourProperties(rvuK[group]) for group in rvuK]
rvuM = pickColumns(cols, rvuL)
if len(rvuM) > 0:
	ttdf_arb = pd.DataFrame.from_dict(rvuM)
	ttdf_arb.to_csv(tour_arb_output, index=False, columns=cols)

#cols = 'UENR,DAG,tour,purpose,mode,weight,Adur,Mdur,zoneA,zoneB,activity_range,trip_range,main_trip_range,outbound_range,inbound_range'.split(',')
cols = 'UENR,DAG,tour,purpose,mode,weight,Adur,Mdur,zoneA,zoneB'.split(',')
rvuJ = [r for r in rvuI if r['day_type'] in ['arbete->arbete', 'arbete->bostad', 'arbete->annat', 'arbete->bostad_fri', 'arbete->bostad_ovr']]  # Workbased
rvuK = groupBy(rvuJ, ['UENR', 'tour'])
rvuL = [WB_TourProperties(rvuK[group]) for group in rvuK]
rvuM = pickColumns(cols, rvuL)
if len(rvuM) > 0:
	ttdf_arb = pd.DataFrame.from_dict(rvuM)
	ttdf_arb.to_csv(tour_WB_output, index=False, columns=cols)
