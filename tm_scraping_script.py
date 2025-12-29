import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import logging
from typing import List, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'
}

def get_page(url: str, retry_count: int = 3) -> BeautifulSoup:
    """Fetch and parse a page with retry logic."""
    for attempt in range(retry_count):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            
            if response.status_code == 200:
                return BeautifulSoup(response.content, 'html.parser')
            else:
                logger.warning(f"Status code {response.status_code} for URL: {url}")
                
        except requests.RequestException as e:
            logger.error(f"Request failed (attempt {attempt + 1}/{retry_count}): {e}")
            
        if attempt < retry_count - 1:
            time.sleep(2 ** attempt)  # Exponential backoff
    
    raise Exception(f"Failed to load page after {retry_count} attempts: {url}")

def extract_matchdays(soup: BeautifulSoup) -> List[str]:
    """Extract matchday numbers from the page."""
    try:
        inline_selects = soup.find_all("div", {"class": "inline-select"})
        
        if len(inline_selects) < 2:
            raise Exception("Could not find matchday selector on page")
        
        md_scrape = list(filter(None, inline_selects[1].text.split('\n')))
        matchdays = [''.join(ch for ch in md.strip() if ch.isdigit()) for md in md_scrape]
        matchdays = [md for md in matchdays if md]  # Remove empty strings
        
        logger.info(f"Found {len(matchdays)} matchdays")
        return matchdays
        
    except Exception as e:
        logger.error(f"Error extracting matchdays: {e}")
        raise

def clean_team_name(text: str) -> str:
    """Clean team name by removing brackets and extra whitespace."""
    # Remove content in brackets/parentheses
    text = re.sub(r"[\(\[].*?[\)\]]", "", text)
    # Remove non-breaking spaces and extra whitespace
    text = text.replace('\xa0', '').replace('\n', '').strip()
    return text

def extract_matches_from_matchday(soup: BeautifulSoup, matchday_num: str) -> List[Dict[str, str]]:
    """Extract all matches from a single matchday page."""
    matches = []
    
    # Find home teams
    home_elements = soup.find_all("td", {
        "class": "rechts hauptlink no-border-rechts hide-for-small spieltagsansicht-vereinsname"
    })
    
    # Find away teams
    away_elements = soup.find_all("td", {
        "class": "hauptlink no-border-links no-border-rechts hide-for-small spieltagsansicht-vereinsname"
    })
    
    # Find results
    result_elements = soup.find_all("span", {"class": "matchresult finished"})
    
    # Validate we have matching counts
    min_count = min(len(home_elements), len(away_elements), len(result_elements))
    
    if min_count == 0:
        logger.warning(f"No matches found for matchday {matchday_num}")
        return matches
    
    if not (len(home_elements) == len(away_elements) == len(result_elements)):
        logger.warning(
            f"Mismatched counts for matchday {matchday_num}: "
            f"Home={len(home_elements)}, Away={len(away_elements)}, Results={len(result_elements)}. "
            f"Using minimum: {min_count}"
        )
    
    # Extract match data
    for i in range(min_count):
        try:
            # Extract and clean home team
            home_text = home_elements[i].text
            home_parts = re.split(r'\t+', home_text)
            home_team = clean_team_name(home_parts[1] if len(home_parts) > 1 else home_parts[0])
            
            # Extract and clean away team
            away_text = away_elements[i].text.rstrip('\t')
            away_parts = re.split(r'\t+', away_text)
            away_team = clean_team_name(away_parts[0])
            
            # Extract result
            result = result_elements[i].text.strip().replace(':', '-')
            
            matches.append({
                'Matchday': matchday_num,
                'Home Team': home_team,
                'Score': result,
                'Away Team': away_team
            })
            
        except Exception as e:
            logger.error(f"Error extracting match {i} from matchday {matchday_num}: {e}")
            continue
    
    return matches

def scrape_league_results(league: str, season_id: int, output_file_prefix: str):
    """Scrape all matches for a given league and season."""
    logger.info(f"Starting scrape for league={league}, season={season_id}")
    
    # Get initial page to find matchdays
    base_url = f"https://www.transfermarkt.com/{league}/spieltag/wettbewerb/IR1/"
    initial_url = f"{base_url}/saison_id/{season_id}"
    
    try:
        initial_soup = get_page(initial_url)
        matchdays = extract_matchdays(initial_soup)
        
        if not matchdays:
            raise Exception("No matchdays found")
        
    except Exception as e:
        logger.error(f"Failed to initialize scraping: {e}")
        raise
    
    # Scrape each matchday
    all_matches = []
    
    for matchday in matchdays:
        md_url = f"{base_url}plus/?saison_id={season_id}&spieltag={matchday}"
        
        try:
            md_soup = get_page(md_url)
            matches = extract_matches_from_matchday(md_soup, matchday)
            all_matches.extend(matches)
            
            # Rate limiting - be respectful to the server
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Failed to scrape matchday {matchday}: {e}")
            continue
    
    # Create DataFrame
    if not all_matches:
        raise Exception("No matches were extracted")
    
    df = pd.DataFrame(all_matches)
    
    # Add season column and ensure proper data types
    df.insert(0, 'Season', season_id)
    df['Matchday'] = df['Matchday'].astype(int)
    df = df.sort_values(by=['Matchday']).reset_index(drop=True)
    
    # Save to CSV
    output_file = f'{output_file_prefix}_{season_id}.csv'
    df.to_csv(output_file, index=False)
    
    logger.info(f"Successfully saved {len(df)} matches to '{output_file}'")
    logger.info(f"Data summary: {len(df['Matchday'].unique())} matchdays, "
                f"{len(df['Home Team'].unique())} unique teams")

def parse_parameters(file_path: str) -> Dict:
    """Parse parameters from a text file."""
    parameters = {}
    
    try:
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if not line or '=' not in line:
                    continue
                    
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Handle comma-separated lists
                if ',' in value:
                    value = [v.strip() for v in value.split(',')]
                    # Try to convert list items to integers
                    try:
                        value = [int(v) for v in value]
                    except ValueError:
                        pass
                else:
                    # Try to convert to int or float
                    try:
                        value = int(value)
                    except ValueError:
                        try:
                            value = float(value)
                        except ValueError:
                            pass
                
                parameters[key] = value
        
        # Handle nested parameters (keys with dots)
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
        
    except FileNotFoundError:
        logger.error(f"Parameters file not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error parsing parameters: {e}")
        raise

def main():
    """Main execution function."""
    try:
        params = parse_parameters('parameters.txt')
        
        seasons = params.get('seasons', [])
        league = params.get('league', '')
        
        if not seasons:
            raise ValueError("No seasons specified in parameters")
        if not league:
            raise ValueError("No league specified in parameters")
        
        logger.info(f"Starting scrape for {len(seasons)} season(s)")
        
        for season in seasons:
            try:
                scrape_league_results(
                    league=league,
                    season_id=season,
                    output_file_prefix='Data/LOI/league_of_ireland_results'
                )
            except Exception as e:
                logger.error(f"Failed to scrape season {season}: {e}")
                continue
        
        logger.info("Scraping completed")
        
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        raise

if __name__ == '__main__':
    main()