import pandas as pd
import json
import time

ÄRENDE = 'D_AREALL'  # D_ARE eller D_AREALL
A_P = 'D_A_PKT'
B_P = 'D_B_PKT'

UNKNOWN = -99

logg = []
cpus = []

def runAsserts():

	assert "1" in "AB12"
	assert "3" not in "AB12"

	assert minutes(99) == 99
	assert minutes(UNKNOWN) == UNKNOWN
	assert minutes(100) == 60
	assert minutes(130) == 90
	assert minutes(2400) == UNKNOWN

	rows = [{'A':1}, {'A':1}, {'A':2}]
	#assert _.group_by(rows,'A') == {1:[{'A':1},{'A':1}], 2:[{'A':2}]}

	assert ModeHierarchy(['buss','spv','cykel']), 'koll'
	assert ModeHierarchy(['gång','gång','cykel']), 'cykel'
	assert ModeHierarchy(['ånglok','sparkcykel']), 'övrigt'

	# assert ModeRecoded('gång') == 'gång'
	# assert ModeRecoded('buss') == 'koll'
	# assert ModeRecoded('sparkcykel') == 'övrigt'

	# assert mode_lookup[1] == 'gång'
	# assert mode_lookup[2] == 'cykel'

	# assert purpose_lookup[2] == 'Arbete'
	# assert purpose_lookup[3] == 'Skola'

	# assert place_lookup[2] == 'bostad_ovr'
	# assert place_lookup[3] == 'bostad_fri'

	assert region_lookup[1] == 'SAMM'
	assert region_lookup[14] == 'Väst'

	# assert work_lookup[3] == 'arbetar'
	# assert work_lookup[4] == 'övrigt'

# def changeTypes(rows, cols, types):  # types: .=float 1=int A=string
# 	for row in rows:
# 		for i in range(len(cols)):
# 			cell = row[cols[i]]
# 			if cell == 'NA': continue
# 			if types[i] == '1': cell = int(cell)
# 			if types[i] == '.': cell = float(cell)
# 			row[cols[i]] = cell
# 	return rows

def cpu(label): cpus.append([label, time.time()])

def loggCpu():
	last = cpus[0][1]
	for label,t in cpus:
		logg.append(f"cpu {round(1000*(t-last))} ms {label}")
		last = t

def info(title, rvu):
	if len(rvu) == 0: return f"{title}:\n  0 rader\n  0 kolumner\n"
	return f"{title}:\n  {len(rvu)} rader\n  {len(rvu[0])} kolumner\n  {','.join(rvu[0].keys())}\n"

def freq(rvu,col):
	result = {}
	for row in rvu:
		data = row[col]
		if data not in result: result[data] = 0
		result[data] += 1

	result = [[result[key],key] for key in result]
	result.sort()
	result.reverse()
	res = f"  frekvenser för {col}:\n"
	for count,key in result:
		res += f"    {key}: {count}\n"
	return res

#def getLAN(row): return 1

def groupBy(arr, col):
	result = {}
	for row in arr:
		value = row[col] #[str(row[col]) for col in cols]
		#value = ':'.join(value)
		if value not in result: result[value] = [row]
		else: result[value].append(row)
	return result

def homeRoundTrip(r):
	for b in projekt['B']:
		if r[A_P] == b == r[B_P]: return True
	return False

	#r[A_P] == 1 and r[B_P] == 1 or r[A_P] == 2 and r[B_P] == 2 or r[A_P] == 3 and r[B_P] == 3)

def minutes(t):
	if t == 'NA' or t == UNKNOWN or t >= 2400: return UNKNOWN
	hour = t // 100
	minute = t % 100
	return 60 * hour + minute

def makeLookup(filename,a,b) :
	codes = pd.read_csv(koder + filename)
	d = dict(zip(codes[a], codes[b]))
	d['NA'] = 'NA'
	return d

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

# def ModeRecoded(mode):
# 	"""Kodar om tåg, tbana etc till koll"""
# 	if mode == 'tåg': return 'koll'
# 	elif mode == 'tbana': return 'koll'
# 	elif mode == 'spv': return 'koll'
# 	elif mode == 'buss': return 'koll'
# 	elif mode == 'bil': return 'bil'
# 	elif mode == 'pass': return 'pass'
# 	elif mode == 'cykel': return 'cykel'
# 	elif mode == 'gång': return 'gång'
# 	else: return 'övrigt'

def saveLogg():
	logg.append(f"katalog: {projekt['katalog']}")
	logg.append(f"options: {projekt['options']}")
	logg.append(f"purpose: {projekt['purpose']}")
	logg.append(f"A: {projekt['A']}")
	logg.append(f"B: {projekt['B']}")
	logg.append("")

	logg.append(info('rvu.csv', rvuC))
	logg.append(freq(rvuG, 'mode'))
	logg.append(freq(rvuG, 'purpose'))
	logg.append(freq(rvuG, 'UEDAG'))
	logg.append(freq(rvuG, 'D_A_PKT'))
	logg.append(freq(rvuG, 'D_B_PKT'))
	logg.append(freq(rvuG, 'BOST_LAN'))
	logg.append(freq(rvuG, 'region'))

	logg.append(info('aked.csv', aked))
	logg.append(freq(aked, 'tour'))
	logg.append(freq(aked, 'parts'))

	logg.append(info('bked.csv', bked))
	logg.append(freq(bked, 'tour'))
	logg.append(freq(bked, 'parts'))

	loggCpu()
	logg.append("")

	logg.append(f"Exekveringstid: {int(1000 * (time.time() - start))} ms")

	with open(katalog + 'log.txt', 'w', encoding='utf-8') as f:
		f.write("\n".join(logg))

def findTrip(rows,first,last,tour,parts,purpose0, purpose1):
	"""sök upp första purpose0 eller första purpose1 eller längsta aktivitet"""

	include0 = range(first,last+0)
	include1 = range(first,last+1)

	trips0 = [rows[i] for i in include0]
	trips1 = [rows[i] for i in include1]
	if parts == 1: trips0 = trips1

	modes = [row['mode'] for row in trips1]
	mode = ModeHierarchy(modes)

	acts = [t for t in trips0 if t['purpose'] == purpose0]
	if len(acts) > 0: act = acts[0]
	else:
		acts = [t for t in trips0 if t['purpose'] == purpose1]
		if len(acts) > 0: act = acts[0]
		else:
			if len(include1) == 0:
				return None
			if len(include1) == 1: act = rows[include1[0]]
			else:
				if include0[-1] == last: include0.pop()
				arr = [[minutes(rows[i+1]['D_A_KL']) - minutes(rows[i]['D_B_KL']), rows[i]] for i in include0]
				arr.sort(key=lambda a : a[0])
				dur,act = arr[-1]

	result = {}
	result['F'] = first
	result['I'] = rows.index(act)
	result['L'] = last
	result["UENR"] = act["UENR"]
	result['D_A_S'] = rows[first]['D_A_S']
	result['D_B_S'] = act['D_B_S']
	result['purpose'] = act['purpose']
	result[ÄRENDE] = act[ÄRENDE]
	result['mode'] = mode
	result['D_FORD'] = act['D_FORD']
	result['BOST_LAN'] = act['BOST_LAN']
	result['region'] = act['region']
	result['VIKT_DAG'] = act['VIKT_DAG']
	result['tour'] = tour
	result['parts'] = parts
	return result

def stateMachine(rows):
	A = projekt["A"]  # arbetsplatser
	B = projekt["B"]  # bostäder
	a_stack = []
	b_stack = []
	a_tour = 1
	b_tour = 1

	exclude = []

	AB = A + B
	row = rows[0]

	if (row[A_P] not in AB) and (row[B_P] not in AB):
		row = rows[0].copy()
		row[A_P] = B[0]
		rows = [row] + rows

	for i in range(len(rows)):
		row = rows[i]

		if row[A_P] in B:
			b_stack.append(i)

		if row[B_P] in B and len(b_stack) > 0 and b_stack[-1] != i:
			start = b_stack.pop()
			for j in range(start,i+1): exclude.append(j)
			trip = findTrip(rows, start, i, b_tour, 2, 'Arbete', 'Tjänste')
			if trip != None:
				bked.append(trip)
				b_tour += 1

		if row[A_P] in A:
			if i not in exclude:
				a_stack.append(i)

		if row[B_P] in A and len(a_stack) > 0 and a_stack[-1] != i:
			start = a_stack.pop()
			if start not in exclude and i not in b_stack:
				trip = findTrip(rows, start, i, a_tour, 2, 'Tjänste', 'Arbete')
				if trip != None:
					aked.append(trip)
					a_tour += 1

	if "B" in options and "1" in options and len(b_stack) > 0:
		trip = findTrip(rows,b_stack.pop(),len(rows)-1,b_tour,1,'Arbete','Tjänste')
		if trip != None:
			bked.append(trip)

def to_dict(rvu): # Hanterar NA, typer, omvandling till dict. Kan modifieras till att byta kolumnnamn.
	cols = []
	for index, key in enumerate(rvu.items()):
		cols.append(key[0])

	result = []
	for r in rvu.itertuples(index=False):
		hash = {}
		for index in range(len(cols)):
			key = cols[index]
			cell = r[index]
			if cell == 'NA' or key == 'D_A_S' or key == 'D_B_S': hash[key] = cell
			elif key == 'VIKT_DAG': hash[key] = float(cell)
			else: hash[key] = int(cell)
		result.append(hash)
	return result

def pick (cols,r):
	result = {}
	for col in cols:
		result[col] = r[col]
	return result

cpu('start')
start = time.time()

with open('settings.json') as f: settings = json.load(f)
index = settings["index"]
projekt = settings[index]
options = projekt["options"]
katalog = projekt["katalog"]
ÄRENDE = projekt["purpose"]
koder = katalog + 'koder/'

region_lookup  = makeLookup("region.txt",'lkod','region')
mode_lookup    = makeLookup("färdmedel.txt",'id','grp')
purpose_lookup = makeLookup("ärende_new.txt",'id','grp')
place_lookup   = makeLookup("plats.txt",'id','plats')

runAsserts()

cols = f"VIKT_DAG,D_A_S,D_B_S,UENR,UEDAG,BOST_LAN,{ÄRENDE},D_FORD,D_A_KL,D_B_KL,D_A_SVE,D_B_SVE,D_A_PKT,D_B_PKT".split(',') # BOST_S
#cols = f"VIKT_DAG,D_A_S,D_B_S,UENR,UEDAG,BOST_S,{ÄRENDE},D_FORD,D_A_KL,D_B_KL,D_A_SVE,D_B_SVE,D_A_PKT,D_B_PKT".split(',') # BOST_S

converters = {}
for col in cols: converters[col] = lambda x : x  # leave every cell as a string
cpu('init')

rvuA = pd.read_csv(katalog + 'rvu.csv', usecols=cols, converters=converters)
cpu('read_csv')

rvuC = to_dict(rvuA)
cpu('to_dict')

for r in rvuC:
	r['purpose'] = purpose_lookup[r[ÄRENDE]]
	r['mode']    = mode_lookup[r['D_FORD']]
cpu('lookup')

rvuD = [r for r in rvuC if r['D_A_SVE'] == 1 and r['D_A_SVE'] == 1] # filtera bort utrikesresor
rvuF = [r for r in rvuD if r['UEDAG'] <= 7] # filtrera fram veckodagar.
rvuG = [r for r in rvuF if not homeRoundTrip(r)] # filtrera bort rundresor
cpu('filter')

for row in rvuG: row["region"] = -1 if row["BOST_LAN"] == -1 else region_lookup[row["BOST_LAN"]]
cpu('region')

rvuH = groupBy(rvuG, 'UENR')
cpu('group_by')

aked = []
bked = []
for uenr in rvuH:
	if uenr == 20110621031:
	#if uenr == 20110341051:
	#if uenr == 20110131010:
		z=99
	print(uenr)
	stateMachine(rvuH[uenr])
cpu('stateMachine')

if "A" in options: pd.DataFrame.from_dict(aked).to_csv(katalog + 'aked_python.csv', index=False)
if "B" in options: pd.DataFrame.from_dict(bked).to_csv(katalog + 'bked_python.csv', index=False)
cpu('to_csv')

saveLogg()
