"""
Name:  Henry Cheung
Email: henry.cheung72@myhunter.cuny.edu
Resources:  
"""

import numpy as np
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from flask import Flask

app = Flask(__name__)

mapHTML = None

@app.route('/')
def index():
    return mapHTML._repr_html_()

def dataCleanUp():
    #DOMH CAMIS and Open_Restaurant_App Food Service Establishment Permit # same. Use this to merge.
    inspectResult = pd.read_csv("DOHMH_New_York_City_Restaurant_Inspection_Results_Original.csv")
    inspectResult = inspectResult[pd.notnull(inspectResult['DBA'])] #Remove rows where DBA (Restaurant Name) is null
    inspectResult = inspectResult[pd.notnull(inspectResult['Longitude'])] #remove rows where Longitude is null
    inspectResult = inspectResult[pd.notnull(inspectResult['Latitude'])] #remove rows where Latitude is null
    inspectResult = inspectResult[inspectResult['Longitude'] != 0] #remove rows where longitude == 0
    inspectResult = inspectResult[inspectResult['Latitude'] != 0] #remove rows where latitude == 0
    inspectResult = inspectResult[pd.notnull(inspectResult['CUISINE DESCRIPTION'])] # remove all entries with no cusine description
    inspectResult = inspectResult[pd.notnull(inspectResult['SCORE'])] #removes all entries that does not have a score. Cant predict if both GRADE and SCORE are empty
    inspectResult['INSPECTION DATE'] = pd.to_datetime(inspectResult['INSPECTION DATE'])
    inspectResult.sort_values(by=['INSPECTION DATE'], inplace=True, ascending=False) #Sort by most recent dates first
    inspectResult['newGrade'] = inspectResult.apply(lambda inspectResult: 'A' if 13 >= inspectResult['SCORE'] >= 0 else ('B' if 27 >= inspectResult['SCORE'] >= 14 else 'C'), axis = 1)
    inspectResult['GRADE'].fillna(inspectResult['newGrade'], inplace = True)
    inspectResult = inspectResult.drop(columns = ['newGrade', 'GRADE DATE', 'VIOLATION CODE', 'RECORD DATE'], axis = 1)
    inspectResult['CAMIS'] = inspectResult['CAMIS'].astype(str)

    inspectRes = inspectResult
    print(type(inspectRes['CAMIS'][0]))
    
    #Covid outside seating applications
    filteredCol2 = ['Restaurant Name', 'Legal Business Name', 'Doing Business As (DBA)', 'Business Address', 'Approved for Sidewalk Seating', 'Approved for Roadway Seating','Food Service Establishment Permit #']
    covidApp = pd.read_csv("Open_Restaurant_Applications.csv", usecols = filteredCol2)
    covidApp = covidApp.rename(columns = {'Food Service Establishment Permit #' : 'CAMIS'})
    cApp = covidApp
    print(type(covidApp['CAMIS'][0]))
    cApp.to_csv("output5.csv", index=False)
    
    inspectRes.reset_index(drop = True, inplace = True)
    covidApp.reset_index(drop = True, inplace = True)
    #concatCSV = pd.concat([inspectRes, covidApp],axis=1)
    concatCSV = pd.DataFrame.merge(inspectRes, cApp, on='CAMIS')
    concatCSV = concatCSV.drop_duplicates(subset=['CAMIS'], keep='first')
    concatCSV = concatCSV.drop(columns = ['Community Board', 'Council District', 'Census Tract', 'BIN', 'BBL', 'NTA', 'Restaurant Name', 'Legal Business Name', 'Doing Business As (DBA)', 'Business Address'], axis=1)
    concatCSV = concatCSV[pd.notnull(concatCSV['SCORE'])]
    concatCSV['Approved for Sidewalk Seating'].fillna('N/A', inplace = True)
    concatCSV['Approved for Roadway Seating'].fillna('N/A', inplace = True)
    concatCSV.to_csv("output6.csv", index=False)
    return concatCSV



def generateMap(inspectRes):
    count = 0
    NY_map = folium.Map(location=[inspectRes['Latitude'].mean(), inspectRes['Longitude'].mean()], zoom_start=14, control_scale=True)
    mc = MarkerCluster()
    for index,row in inspectRes.iterrows():

        lat = row['Latitude']
        lon = row['Longitude']
        name = row['DBA']
        score = row['GRADE']
        cuisine = row['CUISINE DESCRIPTION']
        address = str(row['BUILDING']) + " " + str(row['STREET']) + " " + str(row['BORO']) + ", NY " + str(row['ZIPCODE'])
        sideSeating = row['Approved for Sidewalk Seating']
        outSeating = row['Approved for Roadway Seating']
        inspecDate = row['INSPECTION DATE']
        violation = row['VIOLATION DESCRIPTION']
        critical = row['CRITICAL FLAG']
        popupText = folium.Popup('<b> Name: </b>' + str(name) + '<br/><b> Score: </b>' + str(score) + '<br/><b> Violation: </b>' + str(violation) + '<br/><b> Critical: </b>' + str(critical) + '<br/><b> Cuisine: </b>' + str(cuisine) + '<br/><b> Address: </b>' + str(address) + '<br/><b> Approved for Sidewalk Seating: </b>' + str(sideSeating) + '<br/><b> Approved for Roadway Seating: </b>' + str(outSeating), max_width = 500) 
        mc.add_child(folium.Marker(location=[lat, lon], popup=popupText))
        
        count += 1
        print(count)

        if count == 248:
            break
        
    NY_map.add_child(mc)
    NY_map.save(outfile ='NY_map1.html')
    return NY_map


if __name__ == '__main__':
    inspectRes = dataCleanUp()
    mapHTML = generateMap(inspectRes)
    
    app.run(debug=True)
    
    
