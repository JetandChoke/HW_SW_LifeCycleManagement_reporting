#!/usr/bin/env/python3.8

import requests
import json
import base64
import pandas as pd
from datetime import timedelta, datetime
from dateutil.relativedelta import *

## Get the portal access token from https://www.arista.com/en/users/profile
token = 'Insert your token here'
url = 'https://www.arista.com/custom_data/bug-alert/alertBaseDownloadApi.php'

# IB DATA REQUIRED AS A TEMPLATE FOR THE REPORT
file1 = 'IB_DB.csv'
true_up = 'trueup-2021-12-05.csv'

hw_csv_file = 'HW.csv'
sw_csv_file = 'SW.csv'
release_info = 'Release info.csv' # REQUIRED AS ALERT API DOESN'T PROVIDE RELEASE DATE INFO JUST YET

true_up_data = pd.read_csv(file1)
df3 = pd.DataFrame(true_up_data)

hw_src_data = pd.read_csv(hw_csv_file)
df1 = pd.DataFrame(hw_src_data)

HW = df3['ComponentName'].drop_duplicates().sort_values()
HW_list = []

creds = (base64.b64encode(token.encode())).decode("utf-8")
jsonpost = {'token_auth': creds,'file_version':'2'}
result = requests.post(url, data=json.dumps(jsonpost))
data = json.loads(result.text)

for i in HW:
    if str(i).startswith('DCS-') or str(i).startswith('750'):
        print(f'HW_list is appended by {i}')
        HW_list.append(str(i))

##  REMOVE MODELS IN LCM WHICH ARE NOT PRESENT IN THE LATEST TRUEUP
for i, row in df1.iterrows():
    found = False
    device = row['Model']
    print(f'working on {device}')
    for item in HW_list:
        print(f'matching with {item}')
        if device == item:
            found = True
            print(f'found match {device} and {item}')
            break
        elif device == '130' or device == '130E' or device == '230' or device == '260':
            print(f'found AP {device}, skipping')
            found = True
            break
        # else:
        #     found = False
    if not found:
        print(f'going to drop {device} from the list')
        df1.drop(i, inplace = True)
print(df1)


##  GO THROUGH INSTALL BASE MODEL LIST.
##  GO THROUGH THE HW LIFECYCLE LCM CSV.
##  IF LCM CONTAINS ANY MODELS WHICH ARE NOT IN THE LATEST TRUEUP REPORT, REMOVE THAT MODEL FROM LCM.
##  IF THE LATEST LCM REPORT CONTAINS ANY NEW MODELS, WHICH DO NOT EXIST IN THE HW LCM REPORT TEMPLATE - ADD THEM.

for item in HW_list:
    found = False
    for i, row in df1.iterrows():
        found = False
        device = row['Model']
        if device == item:
            ## LCM MODEL IS IN TRUEUP
            found = True
            break
    if not found:
            ## LCM DOES NOT HAVE THE MODEL FROM THE LATEST TRUEUP
            print(f'New model in TRUEUP {item}')
            new_row = {'Model': item}
            print(f'did not find {item} in LCM, adding {item}')
            df1 = df1.append(new_row, ignore_index = True)
print(f'adding new models to LCM:')
print(df1)

### Working on HW file
missing_list = list()
for i, row in df1.iterrows():
    found = False
    device = row['Model']
    print(f'working on {device}')

    for item in data['hardwareLifecycles']:
        modelName = item['modelName']
        #print(f'modelName: {modelName}')
        if device == modelName:
            #print(f'found device: {device}')
            EofS = item['endOfSale']
            #print(f'EofS: {EofS}')
            df1.iloc[i]['End of Sales Date'] = item['endOfSale']
            df1.iloc[i]['End of SW Security Support Date'] = item['endOfLife']
            df1.iloc[i]['End of Support Date'] = item['endOfTACSupport']
            found=True
            df1.to_csv('result_hw.csv', index=False)
            break
    if not found:
        ### it means EoS/EoL is not reached yet
        missing_list.append(device)
        # df1.iloc[i]['End of Sales Date'] = ''
        # df1.iloc[i]['End of SW Security Support Date'] = ''
        # df1.iloc[i]['End of Support Date'] = ''
        # df1.to_csv(hw_csv_file, index=False)
print(f'Model which is not EoS just yet, disregard APs: {missing_list}')
### We are done with HW data now
print(f'result hw file:')
print(df1)

## COUNT HOW MANY TIMES EACH MODEL IS MENTIONED IN TRUEUP, THERE ARE BETTER WAYS TO DO IT WITH PANDAS, JFYI
df4 = pd.DataFrame(columns=['Model','Count'])
        
for i in HW_list:
    model_count = 0
    for h in df3['ComponentName']:
        if i == h:
            model_count += 1
    print(f'model {i} count {model_count}')
    my_dict = {'Model': i, 'Count': model_count}
    df4.loc[len(df4)] = my_dict
    # df4.iloc[ind]['Model'] = i
    # df4.iloc[ind]['Count'] = model_count
print(df4)
df4.to_csv('result_hw_ib.csv', index=False)

##  COUNT MODEL PER RELEASE IN TRUEUP
SW = df3['Version'].drop_duplicates().sort_values()
SW_list = []
for i in SW:
    #comp_i = str(i[0:4])
    SW_list.append(str(i))
print(f'SW_list: {SW_list}')

df5 = pd.DataFrame(columns = ['Model','SW Release','Count','Vendor Release Date','End of Sales Date','End of SW Security Support Date','End of Support Date'])

for model in HW_list:
    for version in SW_list:
        mode_version_count = 0
        for i, row in df3.iterrows():
            df3_device = row['ComponentName']
            df3_version = row['Version']
            if model == df3_device:
                if version == df3_version:
                    ##  COUNT COMBINATIONS OF HW/SW
                    mode_version_count += 1
                    my_dict = {'Model':model, 'SW Release':version, 'Count':mode_version_count}
        df5.loc[len(df5)] = my_dict
##  REMOVING DUPLICATES FROM DATAFRAME BEFORE QUERYING FOR SW RELEASE INFO
df5.drop_duplicates(inplace = True)

##  POPULATE SW RELEASE INFO FROM Relese info.csv
release_info_data = pd.read_csv(release_info)
df6 = pd.DataFrame(release_info_data)
for i, row in df5.iterrows():
    found = False
    release = row['SW Release']
    for i1, row1 in df6.iterrows():
        release_number = row1['Release Number']
        release_date = row1['Release Date']
        if release == release_number:
            df5.loc[i, 'Vendor Release Date'] = release_date
print(f'final df5: {df5}')

##  POPULATE EoS/EoL info
sw_missing_list = list()
for i1, row in df5.iterrows():
    found = False
    sw = row['SW Release']
    comp_sw = sw[0:4]
    print(f'working on {sw}, {comp_sw}')
    for item in data['softwareLifecycles']:
        version = item['version']
        sw_EofS = item['endOfSupport']
        if comp_sw == version:
            sw_EofSecS = ((datetime.strptime(sw_EofS, "%Y-%m-%d")) + relativedelta(months=-6)).strftime("%Y-%m-%d")
            print(f'sw_EofS: {sw_EofS}')
            # print(f'sw_EofSecS: {sw_EofSecS}')
            df5.loc[i1, 'End of SW Security Support Date'] = sw_EofSecS
            df5.loc[i1, 'End of Support Date'] = sw_EofS
            found=True
            df5.to_csv('result_sw.csv', index=False)
            print(f'{sw} is done...')
            break
    if not found:
        sw_missing_list.append(sw)
print(f'EOS which has no End of Support date just yet: {sw_missing_list}')
print(f'final df5: {df5}')
# ### We are done with SW data now
