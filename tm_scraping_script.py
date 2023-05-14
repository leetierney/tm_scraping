#import packages
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

#Function to scrape results
def scrape_results(league, season):
    #Header to be used in request on site
    headers = {'User-Agent':  'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'}

    #Get structure of page
    page = f"https://www.transfermarkt.co.uk/{league}/spieltag/wettbewerb/IR1/plus/?saison_id={season}&spieltag=1"
    pageTree = requests.get(page, headers=headers)
    pageSoup = BeautifulSoup(pageTree.content, 'html.parser')

    #Find all matchdays in a given season (varies depending on League and Season combination)
    md_scrape = list(filter(None,pageSoup.find_all("div",{"class": "inline-select"})[1].text.split('\n')))

    #md_scrape returns a String, like "1.Matchday", we want to strip away the unnecessary text
    matchdays = []

    for i in range(len(md_scrape)):
	    matchdays.append(''.join(ch for ch in md_scrape[i] if ch.isdigit()))

    matchday_data = []
    
    #Now that we have all of the matchdays for the given League and Season combination, we want to pull all data for all seasons
    for i in range(len(matchdays)):
        page = f"https://www.transfermarkt.co.uk/{league}/spieltag/wettbewerb/IR1/plus/?saison_id={season}&spieltag={matchdays[i]}"
        pageTree = requests.get(page, headers=headers)
        pageSoup = BeautifulSoup(pageTree.content, 'html.parser')

        matchday_data.append(pageSoup)

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
        
        home_team[i][j] = home_team[i][j][1].strip()

    #Find the away teams, and append to their own list
    away_team = []

    for i in range(len(matchday_data)):
        away_team.append(matchday_data[i].find_all("td",
                        {"class": "hauptlink no-border-links no-border-rechts hide-for-small spieltagsansicht-vereinsname"}))
        
    for i in range(len(away_team)):
        for j in range(len(away_team[i])):
            away_team[i][j] = re.split(r'\t+', away_team[i][j].text.rstrip('\t'))[0].strip()
    
    pass

def main():
    league = 'sse-airtricity-league-premier-division'
    season = 2021
    print(scrape_results(league, season))

if __name__ == "__main__":
    main()