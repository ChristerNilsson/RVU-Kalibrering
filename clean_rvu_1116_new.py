# Process för att läsa in och rensa delresor
# Inläsning av data

import pandas as pd
import numpy as np
import json

from datetime import datetime, time, timedelta

with open('settings.json') as f:
	settings = json.load(f)

root = settings['root']
input = root + settings['input']
output = root + settings['output']
rvu_input = input + settings['rvu']
tour_arb_output = output + "tour_arb.csv"
koder = root + settings['koder']
skiprows = settings['skiprows']
nrows = settings['nrows']

cols = "UENR,BOST_LAN,D_ARE,D_FORD,D_A_KL,D_B_KL,UEDAG,VIKT_DAG,D_A_S,D_B_S,D_A_SVE,D_B_SVE,D_A_PKT,D_B_PKT".split(',')
rvu_dr_raw_1116= pd.read_csv(rvu_input, usecols=cols)

rvu_dr_raw_1116['years'] = '11-16'
rvu_dr_raw = rvu_dr_raw_1116

# Koda om färdmedel, ärende etc
# 
# Vi kodar om resvaneundersökningens sifferkoder för till exempel färdmedel till de grupperade färdmedel som används i Sampers. Detsamma görs för ärende, plats (dvs bostad, arbetsplats, skola, annat). Vi kodar också på Sampers-region istället för län så att vi kan titta på eventuella skillnader mellan regionerna senare.
# 
# I RVU:erna är skola ett ärende, medan Sampers skiljer på skola för olika åldersgrupper. Här använder vi samma uppdelning som i skattningen, dvs i tre grupper: Grundskola för åldrarna 6-15 år, gymnasium för 16-18 år och vuxenutbildning för 19 år och uppåt.

# Read and define lookup tables for survey codes

mode_codes = pd.read_csv(koder + "fm_kod.txt", sep='\t')
mode_lookup = dict(zip(mode_codes["id"], mode_codes["grp"]))

purpose_codes = pd.read_csv(koder + "ärende_kod_gen.txt", sep='\t')
purpose_lookup = dict(zip(purpose_codes["id"], purpose_codes["grp"]))

place_codes = pd.read_csv(koder + "plats_kod.txt", sep='\t')
place_lookup = dict(zip(place_codes["id"], place_codes["plats"]))

region_codes = pd.read_csv(koder + "region_kod.txt", sep=',')
region_lookup = dict(zip(region_codes["lkod"], region_codes["region"]))

work_codes = pd.read_csv(koder + "arbete_kod.txt", sep='\t')
work_lookup = dict(zip(work_codes["kod"], work_codes["status"]))


def ConvertToTime(year: int, inttime:int):
    if (inttime<2400)&(inttime!=99):
        hour = int(inttime/100)
        minute = int(inttime%100)
        timeOfDay = datetime(year=year, month = 1, day=1, hour=hour,minute=minute)
        return timeOfDay- datetime(2021,1,1)
    else:
        return -99

# att filtera ut missing values för dessa variabler
rvu_cleaned=rvu_dr_raw[rvu_dr_raw.D_A_SVE.eq(1.0)&rvu_dr_raw.D_B_SVE.eq(1.0)] # filtera ut utrikesresor
rvu_cleaned=rvu_cleaned[~((rvu_cleaned.D_A_PKT.eq(1)&rvu_cleaned.D_B_PKT.eq(1))|(rvu_cleaned.D_A_PKT.eq(2)&rvu_cleaned.D_B_PKT.eq(2))|(rvu_cleaned.D_A_PKT.eq(3)&rvu_cleaned.D_B_PKT.eq(3)))]#filtera ut och rundresor

rvu_cleaned=rvu_cleaned.replace(np.nan,-99)
year=2021


rvu_dr = rvu_cleaned["UENR,VIKT_DAG,UEDAG,years,D_A_S,D_B_S".split(',')].copy()
rvu_dr=rvu_dr.rename(columns={"D_A_S":"D_A_DESO","D_B_S":"D_B_DESO"})   #1116
rvu_dr["mode"] = rvu_cleaned.apply(lambda x: mode_lookup[x["D_FORD"]], axis=1)
rvu_dr["purpose"] = rvu_cleaned.apply(lambda x: purpose_lookup[x["D_ARE"]], axis=1)
rvu_dr["place_orig"] = rvu_cleaned.apply(lambda x: place_lookup[x["D_A_PKT"]], axis=1)
rvu_dr["place_dest"] = rvu_cleaned.apply(lambda x: place_lookup[x["D_B_PKT"]], axis=1)
rvu_dr['start_time'] = rvu_cleaned["D_A_KL"].apply(lambda x: ConvertToTime(year,x))
rvu_dr['end_time'] = rvu_cleaned["D_B_KL"].apply(lambda x: ConvertToTime(year,x))
rvu_dr["trv_region"] = rvu_cleaned.apply(lambda x: region_lookup[x["BOST_LAN"]], axis=1)

# Eftersom vi inte vill släpa med oss all individ-information genom de funktioner som vi använder för att skapa resedagböcker och turer så skapar vi här en tabell med individinformation som vi sedan kan koda på turerna igen.

rvu_ind = rvu_dr.groupby('UENR',as_index=False).nth(0)['UENR,trv_region,UEDAG'.split(',')]
n_ind_dr = rvu_dr.groupby('UENR').ngroups
print(f'{rvu_dr.shape[0]} observations for {n_ind_dr} individuals in the cleaned dataset')

# skapa delresor om resan inte eller börja hemma

def complete_tours(data):

    data = data.reset_index()
    complete_data = data.copy(deep=True)
    complete_data["real"] = True
    offset = 0

    for index, row in data.iterrows():

        user_id = row["UENR"]

        # first row special case, if tour is not starting at home -> add from home trip
        if index == 0:
            if row["place_orig"] != "bostad":
                extra_row = row.copy(deep=True)
                extra_row["place_orig"] = "bostad"
                extra_row["place_dest"] = "annat"
                extra_row["D_A_DESO"] = row["D_A_DESO"]
                extra_row["D_B_DESO"] = row["D_A_DESO"]
                extra_row["start_time"] = row["start_time"]
                extra_row["end_time"] = row["start_time"]

                extra_row["real"] = False
                data_add = complete_data[:1].append(extra_row, ignore_index=True)
                complete_data = pd.concat([data_add[1:], complete_data], ignore_index=True)
                offset += 1


        if index > 0:
            previous_row = data.iloc[index - 1]
            previous_user_id = previous_row["UENR"]

            if user_id != previous_user_id:

                # if tour is not starting from home -> add trip from home
                if row["place_orig"] != "bostad":
                    extra_row = row.copy(deep=True)
                    extra_row["place_orig"] = "bostad"
                    extra_row["place_dest"] = "annat"
                    extra_row["D_A_DESO"] = row["D_B_DESO"]
                    extra_row["D_B_DESO"] = row["D_A_DESO"]
                    extra_row["end_time"] = row["start_time"]
                    extra_row["real"] = False
                    data_add = complete_data[:index + offset].append(extra_row, ignore_index=True)
                    complete_data = pd.concat([data_add, complete_data[index + offset:]], ignore_index=True)
                    offset += 1

        # last row special case, if tour is not ending at home -> add back to home trip
        if index == len(data) - 1:
            if row["place_dest"] != "bostad":
                extra_row = row.copy(deep=True)
                extra_row["place_orig"] = "annat"
                extra_row["place_dest"] = "bostad"
                extra_row["D_A_DESO"] = row["D_B_DESO"]
                extra_row["D_B_DESO"] = row["D_A_DESO"]
                extra_row["start_time"] = row["end_time"]

                extra_row["real"] = False
                data_add = complete_data[:index + offset + 1].append(extra_row, ignore_index=True)
                complete_data = pd.concat([data_add, complete_data[index + offset + 1:]], ignore_index=True)
            break

        next_row = data.iloc[index + 1]
        next_user_id = next_row["UENR"]

        if user_id == next_user_id:
            # if next tour trip is starting from home but current tour trip is not ending at home -> add back to home trip
            if next_row["place_orig"] == "bostad" and row["place_dest"] != "bostad":
                extra_row = row.copy(deep=True)
                extra_row["place_orig"] = "annat"
                extra_row["place_dest"] = "bostad"
                extra_row["D_A_DESO"] = row["D_B_DESO"]
                extra_row["D_B_DESO"] = row["D_A_DESO"]
                extra_row["start_time"] = row["end_time"]
                extra_row["real"] = False
                data_add = complete_data[:index + offset + 1].append(extra_row, ignore_index=True)
                complete_data = pd.concat([data_add, complete_data[index + offset + 1:]], ignore_index=True)
                offset += 1

        else:
            # if tour is not ending at home -> add back to home trip
            if row["place_dest"] != "bostad":
                extra_row = row.copy(deep=True)
                extra_row["place_orig"] = "annat"
                extra_row["place_dest"] = "bostad"
                extra_row["D_A_DESO"] = row["D_B_DESO"]
                extra_row["D_B_DESO"] = row["D_A_DESO"]
                extra_row["start_time"] = row["end_time"]
                extra_row["real"] = False
                data_add = complete_data[:index + offset + 1].append(extra_row, ignore_index=True)
                complete_data = pd.concat([data_add, complete_data[index + offset + 1:]], ignore_index=True)
                offset += 1

    return complete_data


complete_rvu_dr=complete_tours(rvu_dr)

# Skapa resedagbok av delresor
# 
# Vi börjar med att gruppera delresorna per individ. För varje grupp körs funktionen `CreateDiary` som är definierad i filen `create_diary.py`. I den funktionen läggs det in aktiviteter före, mellan och efter delresorna så att hela dagen är fylld av antingen resor eller aktiviteter. Först läggs en hemma-, arbete- eller övrigt-aktivitet till i början, beroende på var individien startar sin dag. Vi noterar den informationen i utdata för att senare kommer vi att sortera bort resor som inte startat och slutat hemma. För varje resa läggs sedan en aktivitet till efter resan som börjar när resan slutar. Ärendet definieras av det ärende som uppgetts för resan. Sluttiden sätts till starttiden för nästa resa. Den sista aktiviteten får sluttid 23.59 utom i de fall då resandet pågår till efter midnatt. Då sätts den sista aktiviteten till en minut efter start.
#
# Vi kommer senare att använda den här utökade listan av resor och aktiviteter för att kunna se när olika aktiviteter utförs och för att kunna definiera huvudresans ärende efter vilken aktivitet som är längst i de fall det inte finns någon arbetsresa eller tjänsteresa.

def CreateDiary(trip_list:pd.DataFrame):
    ## ToDo: Identify work based tours    

    idx = 1
    tour_id = 1
    day_type = trip_list.iloc[0]['place_orig'] + ' -> ' + trip_list.iloc[-1]['place_dest']
    cross_midnight = False
    
    # First, create a morning activity, wherever the person starts their morning (usually at home, sometimes somewhere else)
    at_home_morning = {
        'act_id': idx,
        'tour_id': tour_id,
        'day_type': day_type,
#        'type': 'ärende',
        'purpose': trip_list.iloc[0]['place_orig'],
        'mode': 'aktivitet',
        'start_time': trip_list.iloc[0]['start_time'],#timedelta(),
        'end_time': trip_list.iloc[0]['end_time'],#timedelta(),
        'cross_midnight': cross_midnight,
        'weight': trip_list.iloc[0]['VIKT_DAG'],
        'zoneA':trip_list.iloc[0]['D_A_DESO'],
        'zoneB':trip_list.iloc[0]['D_B_DESO'],
        'real':trip_list.iloc[0]['real']
        }
    activities = []

    activities.append(at_home_morning)
    for index, row in trip_list.iterrows():
        trip_start =  row['start_time']
        trip_end = row['end_time']
        prev_act_end = activities[idx - 1]['end_time']

        # When someone starts a trip after midnight
        if(trip_start < prev_act_end):
            cross_midnight = True
            trip_start = trip_start + timedelta(days = 1)

        # Either because trip crosses midnight, or both start and end next day
        if(trip_end < trip_start):
            cross_midnight = True
            trip_end = trip_end + timedelta(days = 1)

        act_start = trip_end

        # Previous activity ends when this trip starts
        # add the end time to it
        activities[idx - 1]['end_time'] = trip_start
        
        # Identify trips that end up at home
        purpose = row['purpose']
        end_tour = False
        if(row['place_dest'] == 'bostad'):
            purpose = 'bostad'
            end_tour = True

        # Add the trip to the diary
        trip = {
        'act_id': idx + 1,
        'tour_id': tour_id,
        'day_type': day_type,
        'purpose': purpose,
        'mode': row['mode'],
        'start_time': trip_start,
        'end_time': trip_end,
        'cross_midnight': cross_midnight,
        'weight': row['VIKT_DAG'],
        'zoneA':row['D_A_DESO'],
        'zoneB':row['D_B_DESO'],
        'real':row['real']
        }
        activities.append(trip)
        idx = idx + 1

        # Add the next activity to the diary
        act = {
        'act_id': idx + 1,
        'tour_id': tour_id,
        'day_type': day_type,
        'purpose': purpose,
        'mode': 'aktivitet',
        'start_time': act_start,
        'end_time': act_start,
        'cross_midnight': cross_midnight,
        'weight': row['VIKT_DAG'],
        'zoneA':row['D_A_DESO'],
        'zoneB':row['D_B_DESO']
        }
        activities.append(act)
        idx = idx + 1

        if(end_tour):
            tour_id += 1
    # End of loop over trips
    
    # If last activity starts before midnight
    # set its end time to midnight, othewise leave it be
    if(activities[idx - 1]['end_time'] <= timedelta(hours=24)):
        activities[idx - 1]['end_time'] = timedelta(hours=23, minutes=59)

    # Transform the list of activities to a dataframe
    df = pd.DataFrame(activities)
    df['duration'] = df['end_time'] - df['start_time']
#    df['duration_str'] = df['duration'].apply(str)
    return df


diary = complete_rvu_dr.groupby('UENR').apply(CreateDiary)
diary = diary.reset_index()
diary.drop('level_1', axis='columns', inplace=True)

# Eftersom vi inte vill släpa med oss all individ-information genom de funktioner som vi använder för att skapa resedagböcker och turer så skapar vi här en tabell med individinformation som vi sedan kan koda på turerna igen.
# Vi definierar en konstant, interval_len, definierar hur många minuter varje tidsintervall är. De använder vi i histogrammen senare i dokumentet. time_of_day är en uppräkning av tiden på dagen för början på varje tidsinterval. Tiden anges i timmar (flyttal, dvs 10:30 blir 10.5)

interval_len = 30

homebased_diaries= diary[diary.day_type.eq('bostad -> bostad')]


# Färdmedelshierarki enl Staffan Algers
# modifierat så att tåg ingår i koll
# indata: en lista av alla fm under resan
# utdata: huvudfm
def ModeHierarchy(modes):
  if ('tåg' in modes.values):
    return 'koll'
  elif ('tbana' in modes.values):
    return 'koll'
  elif ('spv' in modes.values):
    return 'koll'
  elif ('buss' in modes.values):
    return 'koll'
  elif ('bil' in modes.values):
    return 'bil'
  elif ('pass' in modes.values):
    return 'pass' 
  elif ('cykel' in modes.values):
    return 'cykel'
  elif ('gång' in modes.values):
    return 'gång'
  else:
    return 'övrigt'


# Kodar om tåg, tbana etc till koll
def ModeRecoded(mode):
  if mode == 'tåg':
    return 'koll'
  elif mode == 'tbana':
    return 'koll'
  elif mode == 'spv':
    return 'koll'
  elif mode == 'buss':
    return 'koll'
  elif mode == 'bil':
    return 'bil'
  elif mode == 'pass':
    return 'pass' 
  elif mode == 'cykel':
    return 'cykel'
  elif mode == 'gång':
    return 'gång'
  else:
    return 'övrigt'


# Gör om tid-från-midnatt till tidsperiod
def ToTimestep(t:timedelta, length):
  return int(t.seconds / 60 // length)


def RangeFromStartEnd(start, end, interval_length):
  ranges = []
  s = ToTimestep(start, interval_length);
  e = 1 + ToTimestep(end, interval_length);
  if(e <= s):
    # Special case when activity crosses midnight
    e_m = 1 + ToTimestep(timedelta(hours=23, minutes=59), interval_length)
    s_m = ToTimestep(timedelta(hours=24), interval_length)
    ranges.append(range(s, e_m))
    ranges.append(range(s_m, e))
  else:
    ranges.append(range(s,e))
  return ranges


def TourProperties(tour_diary:pd.DataFrame, int_length):

  all_activities = tour_diary[tour_diary['mode'] == 'aktivitet']
  activities = all_activities[all_activities['purpose'] != 'bostad']

  trips = tour_diary.loc[tour_diary['mode'] != 'aktivitet']
  uenr = trips.iloc[0]['UENR']
  tour_id = trips.iloc[0]['tour_id']
  weight = trips.iloc[0]['weight']
  mode = ModeHierarchy(trips['mode'])
  zoneA=trips.iloc[0]['zoneA']
  mainmode_trips = trips[trips['mode'].apply(ModeRecoded) == mode]
  main_zone = tour_diary[tour_diary['purpose'] != 'bostad']
  if(len( main_zone.index) != 0):
    zone= main_zone.loc[main_zone['duration'].idxmax()]
    zoneB=zone['zoneB']
  else:
    zone=tour_diary.loc[tour_diary['duration'].idxmax()]
    zoneB=zone['zoneB']

  # Turer som inte har någon aktivitet definieras som rundturer.
  if(len(activities.index) == 0):

    act_range = RangeFromStartEnd(trips.iloc[0]['start_time'], trips.iloc[-1]['end_time'], int_length)

    tour = {
#        'UENR': uenr,
#        'tour_id': tour_id,
        'purpose': trips.iloc[0]['purpose'] + '_rundtur',
        'mode': mode,
        'weight': weight,
        'act_duration': trips['duration'].sum(),
        'mainmode_duration': trips['duration'].sum(),
        'split_act': False,
        'activity_range': act_range,
        'trip_range': act_range,
        'main_trip_range':  act_range,
        'outbound_range': [],
        'inbound_range': [],
        'zoneA':trips.iloc[0]['zoneA'],
        'zoneB':trips.iloc[0]['zoneB'],
        #'real':trips.iloc[0]['real']
    }

# Annars är det en tur med ett ärende
  else:
    # Ifall det finns ett tjänste-ärende i turen sätts ärendet till det
    if('Arbete' in activities['purpose'].values):
        purpose = 'Arbete'
        zoneB=activities[activities['purpose']=='Arbete'].iloc[0]['zoneB']
    # Ifall det finns ett arbete-ärende i turen sätts ärendet till det
    elif('Tjänste' in activities['purpose'].values):
        purpose = 'Tjänste'
        zoneB=activities[activities['purpose']=='Tjänste'].iloc[0]['zoneB']
    # Annars välj den längsta aktiviteten som ärende
    else:
        main_activity = activities.loc[activities['duration'].idxmax()]
        purpose = main_activity['purpose']
        #zoneB=main_activity['zoneB']

    # När vi bestämt huvudärende så använder vi alla de aktiviteterna
    acts = activities[activities['purpose'] == purpose]
    act_duration = acts['duration'].sum()
    mainmode_duration = mainmode_trips['duration'].sum()
    split_act = acts.shape[0] > 1
    act_range = []
    for idx, a in acts.iterrows():
      act_range.extend(RangeFromStartEnd(a['start_time'],a['end_time'], int_length))

    # if len(act_range[0]) < 1:
    #   print(uenr)
    #   print(act_range)

    if len(act_range) > 1:
      s_act = act_range[0][0]
      e_act = act_range[-1][-1]
    else:
      if len(act_range[0]) > 1:
        s_act = act_range[0][0]
        e_act = act_range[0][-1]
      elif isinstance(act_range[0],int):
        s_act = act_range
        e_act = s_act
      else:
        s_act = act_range[0][0]
        e_act = s_act


    outbound_range = []
    inbound_range = []
    trip_range = []
    for idx, t in trips.iterrows():
        ranges = RangeFromStartEnd(t['start_time'], t['end_time'], int_length)
        trip_range.extend(ranges)

    main_trip_range = []
    for idx, mt in mainmode_trips.iterrows():
        #print(mt)
        ranges = RangeFromStartEnd(mt['start_time'], mt['end_time'], int_length)
        main_trip_range.extend(ranges)
        s = ranges[0][0]
        if (s <= s_act):
          outbound_range.extend(ranges)
        if (s >= e_act):
          inbound_range.extend(ranges)

 
    tour = {
#        'UENR': uenr,
#        'tour_id': tour_id,
        'purpose': purpose,
        'mode': mode,
        'weight': weight,
        'act_duration': act_duration,
        'mainmode_duration': mainmode_duration,
        'split_act': split_act,
        'activity_range': act_range,
        'trip_range': trip_range,
        'main_trip_range':  main_trip_range,
        'outbound_range': outbound_range,
        'inbound_range': inbound_range,
        'zoneA':zoneA,
        'zoneB':zoneB,
        #'real':real
    }
  return pd.Series(tour)


# Gör om till turer. Tar en stund.
homebased_diaries["start_time"] = pd.to_timedelta(homebased_diaries["start_time"])
homebased_diaries["end_time"] = pd.to_timedelta(homebased_diaries["end_time"])
homebased_diaries["duration"] = pd.to_timedelta(homebased_diaries["duration"])
tours_arb = homebased_diaries.groupby(['UENR','tour_id']).apply(lambda df: TourProperties(df, interval_len))
tours_arb = tours_arb.reset_index()

ttdf_arb = pd.merge(tours_arb['UENR,tour_id,purpose,mode,weight,act_duration,mainmode_duration,split_act,zoneA,zoneB'.split(',')], rvu_ind, how='left', on='UENR')
ttdf_arb.to_csv(tour_arb_output)

