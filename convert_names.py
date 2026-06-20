import os
import argparse

CONVERSION = {'"display_team_name"': '"Team"',
              '"team_name"': '"Team"',
              'Tm': 'Team',
              'Red Sox': 'BOS',
              'Yankees': 'NYY',
              'Orioles': 'BAL',
              'Rays': 'TBR',
              'Blue Jays': 'TOR',
              'White Sox': 'CHW',
              'Royals': 'KCR',
              'Guardians': 'CLE',
              'Indians': 'CLE',
              'Twins': 'MIN',
              'Tigers': 'DET',
              'Angels': 'LAA',
              'Athletics': 'OAK',
              'Mariners': 'SEA',
              'Astros': 'HOU',
              'Rangers': 'TEX',
              'Dodgers': 'LAD',
              'Giants': 'SFG',
              'Padres': 'SDP',
              'Rockies': 'COL',
              'Diamondbacks': 'ARI',
              'D-backs': 'ARI',
              'Cubs': 'CHC',
              'Cardinals': 'STL',
              'Brewers': 'MIL',
              'Pirates': 'PIT',
              'Reds': 'CIN',
              'Mets': 'NYM',
              'Braves': 'ATL',
              'Phillies': 'PHI',
              'Marlins': 'MIA',
              'Nationals': 'WSN',
              '"SD"': '"SDP"',
              '"AZ"': '"ARI"',
              '"SF"': '"SFG"',
              'WSH': 'WSN',
              '"KC"': '"KCR"',
              '"TB"': '"TBR"',
              'CWS': 'CHW',
              'Arizona ': '',
              'Atlanta ': '',
              'Baltimore ': '',
              'Boston ': '',
              'Chicago ': '',
              'Cincinnati ': '',
              'Cleveland ': '',
              'Colorado ': '',
              'Detroit ': '',
              'Houston ': '',
              'Kansas City ': '',
              'Los Angeles ': '',
              'Miami ': '',
              'Milwaukee ': '',
              'Minnesota ': '',
              'New York ': '',
              'Oakland ': '',
              'Philadelphia ': '',
              'Pittsburgh ': '',
              'San Diego ': '',
              'Seattle ': '',
              'San Francisco ': '',
              'St. Louis ': '',
              'Tampa Bay ': '',
              'Texas ': '',
              'Toronto ': '',
              'Washington ': ''}


def get_folder():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--folder", help="input folder")
    return str(parser.parse_args().folder)


def convert_names(file_name):
    lines = []
    with open(file_name, 'r', errors="ignore") as f:
        for line in f:
            if 'MLB' not in line and '---' not in line:
                # it is easier for this exercise to throw out data from players who played for multiple teams
                for key in CONVERSION:
                    if key in line:
                        line = line.replace(key, CONVERSION[key])
                lines.append(line)
    with open(file_name, 'w') as f:
        f.writelines(lines)


def convert_all_files():
    folder = os.path.join('raw_data', get_folder())
    for file_name in os.listdir(folder):
        convert_names(os.path.join(folder, file_name))


if __name__ == '__main__':
    convert_all_files()
