import pandas as pd
import json
import pydash as _
import time

ÄRENDE = 'D_ARE'  # D_ARE eller D_AREALL
A_P = 'D_A_PKT'
B_P = 'D_B_PKT'

UNKNOWN = -99

def runAsserts():

	assert "1" in "AB12"
	assert "3" not in "AB12"

	assert minutes(99) == 99
	assert minutes(UNKNOWN) == UNKNOWN
	assert minutes(100) == 60
	assert minutes(130) == 90
	assert minutes(2400) == UNKNOWN

	rows = [{'A':1}, {'A':1}, {'A':2}]
	assert _.group_by(rows,'A') == {1:[{'A':1},{'A':1}], 2:[{'A':2}]}

	assert ModeHierarchy(['buss','spv','cykel']), 'koll'
	assert ModeHierarchy(['gång','gång','cykel']), 'cykel'
	assert ModeHierarchy(['ånglok','sparkcykel']), 'övrigt'

	# assert ModeRecoded('gång') == 'gång'
	# assert ModeRecoded('buss') == 'koll'
	# assert ModeRecoded('sparkcykel') == 'övrigt'

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
			if cell == 'NA': continue
			if types[i] == '1': cell = int(cell)
			if types[i] == '.': cell = float(cell)
			row[cols[i]] = cell
	return rows

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

def findTrip(rows,first,last,exclude,tour,parts): # första Arbete eller första Tjänste eller längsta aktivitet
	include = [i for i in range(first,last+1) if i not in exclude]
	trips = [rows[i] for i in include]
	acts = [t for t in trips if t['purpose'] == 'Arbete']

	modes = [row['mode'] for row in trips]
	mode = ModeHierarchy(modes)

	if len(acts) > 0: act = acts[0]
	else:
		acts = [t for t in trips if t['purpose'] == 'Tjänste']
		if len(acts) > 0: act = acts[0]
		else:
			if len(include) == 1: act = rows[include[0]]
			else:
				if include[-1] == last: include.pop()
				arr = [[minutes(rows[i+1]['D_A_KL']) - minutes(rows[i]['D_B_KL']), rows[i]] for i in include]
				arr.sort(key=lambda a : a[0])
				dur,act = arr[-1]
	result = _.pick(act,'UENR,D_A_S,D_B_S,purpose,mode,VIKT_DAG,BOST_LAN,region'.split(','))
	result['D_A_S'] = rows[first]['D_A_S']
	result['mode'] = mode
	result['tour'] = tour
	result['parts'] = parts
	return result

def stateMachine(rows):
	A = [4, 5]     # arbetsplatser
	B = [1, 2, 3]  # bostäder
	a_stack = []
	b_stack = []
	a_tour = 1
	b_tour = 1

	exclude = [] # samla in alla index inblandade i arbetsbaserade resor.
	for i in range(len(rows)):
		row = rows[i]
		if row[A_P] in A: a_stack.append(i)
		if row[A_P] in B: b_stack.append(i)
		if row[B_P] in A and len(a_stack) > 0 and a_stack[-1] != i:
			start = a_stack.pop()
			for j in range(start,i+1): exclude.append(j)
			aked.append(findTrip(rows,start,i,[],a_tour,2))
			a_tour += 1
		if row[B_P] in B and len(b_stack) > 0 and b_stack[-1] != i:
			bked.append(findTrip(rows,b_stack.pop(),i,exclude,b_tour,2))
			b_tour += 1

	# if len(a_stack) > 0: aked.append(findTrip(rows,a_stack.pop(),len(rows)-1,a_tour))
	#if "1" in options and len(b_stack) > 0:
	#	bked.append(findTrip(rows,b_stack.pop(),len(rows)-1,include,b_tour,1))

start = time.time()

with open('settings.json') as f: settings = json.load(f)
print(settings)
options = settings['projekt'][0]
katalog = settings['projekt'][1]
koder = katalog + 'koder/'

region_lookup  = makeLookup("region.txt",'lkod','region')
work_lookup    = makeLookup("arbete.txt",'kod','status')
mode_lookup    = makeLookup("färdmedel.txt",'id','grp')
purpose_lookup = makeLookup("ärende.txt",'id','grp')
place_lookup   = makeLookup("plats.txt",'id','plats')

runAsserts()

cols = f"VIKT_DAG,D_A_S,D_B_S,UENR,UEDAG,BOST_LAN,{ÄRENDE},D_FORD,D_A_KL,D_B_KL,D_A_SVE,D_B_SVE,D_A_PKT,D_B_PKT".split(',') # BOST_S

converters = {}
for col in cols: converters[col] = lambda x : x  # leave every cell as a string

rvuA = pd.read_csv(katalog + 'rvu.csv', usecols=cols, converters=converters)
rvuB = rvuA.to_dict('records')
rvuC = changeTypes(rvuB,cols,'.AA1111111111111')

for r in rvuC:
	r['purpose'] = purpose_lookup[r[ÄRENDE]]
	r['mode']    = mode_lookup[r['D_FORD']]

rvuD = [r for r in rvuC if r['D_A_SVE'] == 1 and r['D_A_SVE'] == 1] # filtera bort utrikesresor
rvuF = [r for r in rvuD if r['UEDAG'] <= 7] # filtrera fram veckodagar.
rvuG = [r for r in rvuF if not (r[A_P] == 1 and r[B_P] == 1 or r[A_P] == 2 and r[B_P] == 2 or r[A_P] == 3 and r[B_P] == 3)] # filtrera bort rundresor

for row in rvuG: row["region"] = -1 if row["BOST_LAN"] == -1 else region_lookup[row["BOST_LAN"]]
rvuH = _.group_by(rvuG, 'UENR')

aked = []
bked = []

for uenr in rvuH: stateMachine(rvuH[uenr])

if "A" in options: pd.DataFrame.from_dict(aked).to_csv(katalog + 'aked.csv', index=False)
if "B" in options: pd.DataFrame.from_dict(bked).to_csv(katalog + 'bked.csv', index=False)

print(time.time()-start)
