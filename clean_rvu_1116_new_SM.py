import pandas as pd
import json
import pydash as _

ÄRENDE = "D_ARE" # "D_AREALL"
A_P = 'D_A_PKT'
B_P = 'D_B_PKT'

UNKNOWN = -99

def runAsserts():

	assert ConvertToMinutes(99) == 99
	#assert ConvertToMinutes(UNKNOWN) == UNKNOWN
	assert ConvertToMinutes(100) == 60
	assert ConvertToMinutes(130) == 90
	#assert ConvertToMinutes(2400) == UNKNOWN

	rows = [{'A':1}, {'A':1}, {'A':2}]
	assert _.group_by(rows,'A') == {1:[{'A':1},{'A':1}], 2:[{'A':2}]}

	assert ModeHierarchy(['buss','spv','cykel']), 'koll'
	assert ModeHierarchy(['gång','gång','cykel']), 'cykel'
	assert ModeHierarchy(['ånglok','sparkcykel']), 'övrigt'

	assert ModeRecoded('gång') == 'gång'
	assert ModeRecoded('buss') == 'koll'
	assert ModeRecoded('sparkcykel') == 'övrigt'

	rows = [{'A':1, 'B':2, 'C':3}, {'A':4, 'B':5, 'C':6}]
	#assert pickColumns(['A','C'],rows) == [{'A':1, 'C':3}, {'A':4, 'C':6}]
	#assert renameColumns({'A':'Adam','C':'Cesar'},rows) == [{'Adam':1, 'B':2, 'Cesar':3}, {'Adam':4, 'B':5, 'Cesar':6}]

	assert mode_lookup[1] == 'gång'
	assert mode_lookup[2] == 'cykel'

	# assert purpose_lookup[2] == 'Arbete'
	# assert purpose_lookup[3] == 'Skola'

	# assert place_lookup[2] == 'bostad_ovr'
	# assert place_lookup[3] == 'bostad_fri'

	assert region_lookup[1] == 'SAMM'
	assert region_lookup[14] == 'Väst'

	assert work_lookup[3] == 'arbetar'
	assert work_lookup[4] == 'övrigt'

def changeTypes(rows, cols, types):  # types: .=float 1=int A=string
	for row in rows:
		for i in range(len(cols)):
			cell = row[cols[i]]
			if types[i] == '1': cell = int(cell)   if cell != 'NA' else 'NA'
			if types[i] == '.': cell = float(cell) if cell != 'NA' else 'NA'
			row[cols[i]] = cell
	return rows

def ConvertToMinutes(t):
	if t == 'NA' or t >= 2400: return -99
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

def findTrip(rows,first,last):
	row = rows[first]
	uenr = row['UENR']
	A_SAMS = row['D_A_S']
	B_SAMS = row['D_B_S']
	FRD = mode_lookup[row['D_FORD']]
	ARE = purpose_lookup[row[ÄRENDE]]
	return {'UENR':uenr, 'zoneA':A_SAMS, 'zoneB':B_SAMS, 'purpose':ARE, 'mode':FRD}

def stateMachine(rows):
	A = [4, 5]     # arbetsplatser
	B = [1, 2, 3]  # bostäder
	a_stack = []
	b_stack = []
	for i,row in enumerate(rows):
		# uenr = row['UENR']
		# A_SAMS = row['D_A_S']
		# B_SAMS = row['D_B_S']
		# FRD = mode_lookup[row['D_FORD']]
		# ARE = purpose_lookup[row[ÄRENDE]]
		# if row[A_P] in A: a_stack.append({'UENR':uenr, 'zoneA':A_SAMS, 'zoneB':B_SAMS, 'purpose':ARE, 'mode':FRD})
		# if row[A_P] in B: b_stack.append({'UENR':uenr, 'zoneA':A_SAMS, 'zoneB':B_SAMS, 'purpose':ARE, 'mode':FRD})
		if row[A_P] in A: a_stack.append(i)
		if row[A_P] in B: b_stack.append(i)
		# if row[B_P] in A and len(a_stack) > 0: aked.append(a_stack.pop())
		# if row[B_P] in B and len(b_stack) > 0: bked.append(b_stack.pop())
		if row[B_P] in A and len(a_stack) > 0: aked.append(findTrip(rows,a_stack.pop(),i))
		if row[B_P] in B and len(b_stack) > 0: bked.append(findTrip(rows,b_stack.pop(),i))

with open('settings.json') as f: settings = json.load(f)
projekt = settings['projekt']
koder = projekt + 'koder/'

region_lookup = makeLookup("region.txt",'lkod','region')
work_lookup = makeLookup("arbete.txt",'kod','status')
mode_lookup = makeLookup("färdmedel.txt",'id','grp')
purpose_lookup = makeLookup("ärende.txt",'id','grp')
place_lookup = makeLookup("plats.txt",'id','plats')

runAsserts()

cols = f"VIKT_DAG,UENR,UEDAG,BOST_S,BOST_LAN,{ÄRENDE},D_FORD,D_A_KL,D_B_KL,D_A_S,D_B_S,D_A_SVE,D_B_SVE,D_A_PKT,D_B_PKT".split(',')

converters = {}
for col in cols: converters[col] = lambda x : x  # leave every cell as a string

rvuA = pd.read_csv(projekt + 'rvu.csv', converters=converters) # usecols=cols,
rvuB = rvuA.to_dict('records')
rvuC = changeTypes(rvuB,cols,'.111111111111111')
rvuD = [r for r in rvuC if r['D_A_SVE'] == 1 and r['D_A_SVE'] == 1] # filtera bort utrikesresor
rvuF = [r for r in rvuD if r['UEDAG'] <= 7] # filtrera fram veckodagar.
rvuG = [r for r in rvuF if not (r[A_P] == 1 and r[B_P] == 1 or r[A_P] == 2 and r[B_P] == 2 or r[A_P] == 3 and r[B_P] == 3)] # filtrera bort rundresor

for row in rvuG: row["region"] = -1 if row["BOST_LAN"] == -1 else region_lookup[row["BOST_LAN"]]
rvuH = _.group_by(rvuG, 'UENR')

aked = []
bked = []

for uenr in rvuH: stateMachine(rvuH[uenr])

pd.DataFrame.from_dict(aked).to_csv(projekt + 'aked.csv', index=False)
pd.DataFrame.from_dict(bked).to_csv(projekt + 'bked.csv', index=False)
