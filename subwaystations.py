""" Models NYC Subway Stations and loads station data from the MTA feeds """
import csv
from dataclasses import dataclass


borough_names = {
    'Bx': 'Bronx',
    'Q': 'Queens',
    'M': 'Manhattan',
    'Bk': 'Brooklyn',
    'SI': 'Staten Island'
}

stations = {}
stations_by_borough = {}
stations_by_designation = {}
stations_by_line = {}

routes = {}


@dataclass
class SubwayRoute:
    id: str
    designation: str
    name: str


_routelist = []
_routelist.append(SubwayRoute('MTA NYCT_1', '1', '1'))
_routelist.append(SubwayRoute('MTA NYCT_2', '2', '2'))
_routelist.append(SubwayRoute('MTA NYCT_3', '3', '3'))
_routelist.append(SubwayRoute('MTA NYCT_4', '4', '4'))
_routelist.append(SubwayRoute('MTA NYCT_5', '5', '5'))
_routelist.append(SubwayRoute('MTA NYCT_6', '6', '6'))
_routelist.append(SubwayRoute('MTA NYCT_7', '7', '7'))
_routelist.append(SubwayRoute('MTA NYCT_A', 'A', 'A'))
_routelist.append(SubwayRoute('MTA NYCT_B', 'B', 'B'))
_routelist.append(SubwayRoute('MTA NYCT_C', 'C', 'C'))
_routelist.append(SubwayRoute('MTA NYCT_D', 'D', 'D'))
_routelist.append(SubwayRoute('MTA NYCT_E', 'E', 'E'))
_routelist.append(SubwayRoute('MTA NYCT_F', 'F', 'F'))
_routelist.append(SubwayRoute('MTA NYCT_G', 'G', 'G'))
_routelist.append(SubwayRoute('MTA NYCT_J', 'J', 'J'))
_routelist.append(SubwayRoute('MTA NYCT_L', 'L', 'L'))
_routelist.append(SubwayRoute('MTA NYCT_M', 'M', 'M'))
_routelist.append(SubwayRoute('MTA NYCT_N', 'N', 'N'))
_routelist.append(SubwayRoute('MTA NYCT_Q', 'Q', 'Q'))
_routelist.append(SubwayRoute('MTA NYCT_R', 'R', 'R'))
_routelist.append(SubwayRoute('MTA NYCT_W', 'W', 'W'))
_routelist.append(SubwayRoute('MTA NYCT_Z', 'Z', 'Z'))
_routelist.append(SubwayRoute('MTA NYCT_SI', 'SIR', 'Staten Island Railroad'))
_routelist.append(SubwayRoute('MTA NYCT_0', 'S', '42nd Street Shuttle'))
_routelist.append(SubwayRoute('MTA NYCT_H', 'S', 'Rockaway Park Shuttle'))
_routelist.append(SubwayRoute('MTA NYCT_S', 'S', 'Franklin Avenue Shuttle'))

for route in _routelist:
    routes[route.id] = route


def get_route(designation, line):
    cd = 'unknown'
    if 'S' == designation:
        if 'Rockaway' == line:
            cd = 'H'
        elif 'Franklin Shuttle' == line:
            cd = 'S'
        else:
            cd = '0'
    elif 'SIR' == designation:
        cd = 'SI'
    else:
        cd = designation

    return routes['MTA NYCT_' + cd]


@dataclass
class SubwayStation:
    id: str
    complex_id: str
    gtfs_stop_id: str
    division: str
    line: str
    stop_name: str
    borough: str
    routes: []
    station_type: str
    latitude: float
    longitude: float
    north_label: str
    south_label: str


def loadstationfile():
    with open('data/Stations.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            station = SubwayStation(
                row['Station ID'],
                row['Complex ID'],
                row['GTFS Stop ID'],
                row['Division'],
                row['Line'],
                row['Stop Name'],
                borough_names[row['Borough']],
                [get_route(designation, row['Line'])
                    for designation in row['Daytime Routes'].split()],
                row['Structure'],
                float(row['GTFS Latitude']),
                float(row['GTFS Longitude']),
                row['North Direction Label'],
                row['South Direction Label']
            )
            stations.setdefault(station.id, []).append(station)
            stations_by_borough.setdefault(station.borough, []).append(station)
            stations_by_line.setdefault(station.line, []).append(station)
            for route in station.routes:
                stations_by_designation.setdefault(
                    route.designation, []).append(station)


loadstationfile()

if __name__ == "__main__":
    print('\nSTATIONS BY BOROUGH')
    for borough in sorted(stations_by_borough):
        print('{}: {}'.format(borough, len(stations_by_borough[borough])))

    print('\nSTATIONS BY LINE')
    for line in sorted(stations_by_line):
        print('{}: {}'.format(line, len(stations_by_line[line])))

    print('\nSTATIONS BY DESIGNATION')
    for designation in sorted(stations_by_designation):
        print('{}: {}'.format(designation,
                              len(stations_by_designation[designation])))
