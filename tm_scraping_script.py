import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

headers = {'User-Agent':  'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'}

def scrape_league_results(league, season_id, output_file_prefix):
    #Define the base page and get a response from it
    base_url = f"https://www.transfermarkt.com/{league}/spieltag/wettbewerb/IR1/"
    initial_url = f"{base_url}/saison_id/{season_id}"

    response = requests.get(initial_url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Failed to load page, status code: {response.status_code}. URL: {base_url + league_url}")
    
    pageSoup = BeautifulSoup(response.content, 'html.parser')
    
    #Find all matchdays in a given season (varies depending on League and Season combination)
    md_scrape = list(filter(None,pageSoup.find_all("div",{"class": "inline-select"})[1].text.split('\n')))

    #md_scrape returns a String, like "1.Matchday", we want to strip away the unnecessary text
    matchdays = []

    for i in range(len(md_scrape)):
	    matchdays.append(''.join(ch for ch in md_scrape[i] if ch.isdigit()))
         
    # Ensure we have matchday URLs
    if not matchdays:
        raise Exception("No matchday links found. The page structure might have changed.")

    #Initialise master list
    matchday_data = []
    
    # Initialise lists for storing match data
    home_teams = []
    scores = []
    away_teams = []
    
    for matchday in matchdays:
        md_url = f"{base_url}plus/?saison_id={season_id}&spieltag={matchday}"
        # print(f"Scraping matchday data from: {md_url}")

        response = requests.get(md_url, headers=headers)

        if response.status_code != 200:
            print(f"Failed to load matchday page, status code: {response.status_code}. URL: {md_url}")
            continue

        pageSoup = BeautifulSoup(response.content, 'html.parser')

        matchday_data.append(pageSoup)

    # Extract match results
    matches = pageSoup.find_all('tr', {'class': 'odd'}) + pageSoup.find_all('tr', {'class': 'even'})

    for match in matches:
        home_team = match.find('td', {'class': 'team_a'})
        score = match.find('td', {'class': 'result'})
        away_team = match.find('td', {'class': 'team_b'})
        
        if home_team and score and away_team:
            matchdays.append(matchday_number)
            home_teams.append(home_team.text.strip())
            scores.append(score.text.strip())
            away_teams.append(away_team.text.strip())
            
        else:
            print(f"Skipping a row due to missing data: {match}")  

    #Find the home teams, and append to their own list
    home_team = []

    for i in range(len(matchday_data)):
        home_team.append(matchday_data[i].find_all("td",
                        {"class": "rechts hauptlink no-border-rechts hide-for-small spieltagsansicht-vereinsname"}))
        
    for i in range(len(home_team)):
        for j in range(len(home_team[i])):
            home_team[i][j] = re.split(r'\t+',home_team[i][j].text)
            
            if(len(home_team[i][j]) == 1):
                home_team[i][j].insert(0,'')
        
            home_team[i][j] = re.sub("[\(\[].*?[\)\]]", "", home_team[i][j][1].strip().replace(u'\xa0\n', u'')).lstrip()

    #Find the away teams, and append to their own list
    away_team = []

    for i in range(len(matchday_data)):
        away_team.append(matchday_data[i].find_all("td",
                        {"class": "hauptlink no-border-links no-border-rechts hide-for-small spieltagsansicht-vereinsname"}))
        
    for i in range(len(away_team)):
        for j in range(len(away_team[i])):
            away_team[i][j] = re.sub("[\(\[].*?[\)\]]", "", re.split(r'\t+', away_team[i][j].text.rstrip('\t'))[0].strip().strip().replace(u'\xa0\n', u'')).rstrip()
    
    #Find match results, and append to their own list
    result = []

    for i in range(len(matchday_data)):
        result.append(matchday_data[i].find_all("span",{"class": "matchresult finished"}))
        
    for i in range(len(result)):
        for j in range(len(result[i])):
            result[i][j] = result[i][j].text.replace(':', '-')

    # Create a DataFrame from the lists
    data = {
        'Matchday': matchdays,
        'Home Team': home_team,
        'Score': result,
        'Away Team': away_team
    }
    
    df = pd.DataFrame(data)

    #Ensure we have a Season and Matchday Column
    df['Matchday'] = df['Matchday'].astype(int)

    df = df.set_index('Matchday').apply(lambda x: x.apply(pd.Series).stack()).reset_index().drop('level_1', axis = 1).sort_values(by=['Matchday'])
    df.insert(0, 'Season', season_id)
    
    # Define the output file name based on the season
    output_file = f'{output_file_prefix}_{season_id}.csv'
    
    # Save the DataFrame to a CSV file
    df.to_csv(output_file, index=False)
    
    print(f"Data has been saved to '{output_file}'.")
  
def parse_parameters(file_path):
    parameters = {}

    with open(file_path, 'r') as file:
        for line in file:
            key, value = line.strip().split('=', 1)
            if ',' in value:
                value = [v.strip() for v in value.split(',')]
            else:
                try:
                    value = int(value)
                except ValueError:
                    try:
                        value = float(value)
                    except ValueError:
                        pass
            parameters[key] = value

    # Handle nested parameters
    nested_parameters = {}
    for key, value in parameters.items():
        if '.' in key:
            parent, child = key.split('.', 1)
            if parent not in nested_parameters:
                nested_parameters[parent] = {}
            nested_parameters[parent][child] = value
        else:
            nested_parameters[key] = value

    return nested_parameters

def main():
    params = parse_parameters('parameters.txt')

    seasons = params['seasons']

    league = params['league']

    for season in seasons:
        scrape_league_results(league = league , season_id = season, output_file_prefix = 'Data/LOI/league_of_ireland_results')

if __name__ == '__main__':
    main()