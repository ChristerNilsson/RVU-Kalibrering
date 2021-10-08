ARB = 'Arbete'
TJ = 'Tjänste'
ÖVR = 'Övriga'
REKR = 'Rekr'

GÅNG = 'gång'
BIL = 'bil'
SPV = 'spv'

rows = [
	{'A_SAMS':14800034, 'B_SAMS':14800703, 'FRD':BIL, 'ARE':ARB, 'A_P':1, 'B_P':4, 'A_KL': 720,'B_KL': 745},
	{'A_SAMS':14800703, 'B_SAMS':14800678, 'FRD':GÅNG,'ARE':TJ,  'A_P':4, 'B_P':10,'A_KL': 815,'B_KL': 845},
	{'A_SAMS':14800678, 'B_SAMS':14800703, 'FRD':GÅNG,'ARE':ÖVR, 'A_P':10,'B_P':4, 'A_KL':1045,'B_KL':1120},
	{'A_SAMS':14800703, 'B_SAMS':14800668, 'FRD':SPV, 'ARE':TJ,  'A_P':4, 'B_P':10,'A_KL':1240,'B_KL':1255},
	{'A_SAMS':14800668, 'B_SAMS':14800703, 'FRD':SPV, 'ARE':ARB, 'A_P':10,'B_P':4, 'A_KL':1355,'B_KL':1420},
	{'A_SAMS':14800703, 'B_SAMS':14800034, 'FRD':BIL, 'ARE':ARB, 'A_P':4, 'B_P':1, 'A_KL':1600,'B_KL':1620},
	{'A_SAMS':14800034, 'B_SAMS':14010006, 'FRD':BIL, 'ARE':REKR,'A_P':1, 'B_P':10,'A_KL':1830,'B_KL':1855},
	{'A_SAMS':14010006, 'B_SAMS':14800034, 'FRD':BIL, 'ARE':REKR,'A_P':10,'B_P':1, 'A_KL':2145,'B_KL':2220}
]

B = 1
A = 4

a_stack = []
b_stack = []

for row in rows:
	A_SAMS = row['A_SAMS']
	B_SAMS = row['B_SAMS']
	FRD = row['FRD']
	ARE = row['ARE']
	if row['A_P'] == A: a_stack.append(['ARBETE',A_SAMS,B_SAMS,ARE,FRD])
	if row['A_P'] == B: b_stack.append(['BOSTAD',A_SAMS,B_SAMS,ARE,FRD])
	if row['B_P'] == A and len(a_stack) > 0: print(a_stack.pop())
	if row['B_P'] == B and len(b_stack) > 0: print(b_stack.pop())
