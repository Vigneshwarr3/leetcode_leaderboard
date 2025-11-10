import requests
import json
import datetime
import pandas as pd
#from cookies import cookies
import os

cookies_env = os.getenv('LEETCODE_COOKIES')
    
if isinstance(cookies_env, str):
    try:
        cookies = json.loads(cookies_env)
    except json.JSONDecodeError:
        cookies = {}
else:
    cookies = cookies_env or {}

# Ensure all cookie values are strings
cookies = {k: str(v) for k, v in cookies.items()}

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0'
}

def get_recent_ac_submissions(username, limit=20):
    """
    Fetches recent ACCEPTED submissions using the 'recentAcSubmissionList' query.
    """
    url = "https://leetcode.com/graphql"
    
    # This payload matches your desired output
    payload = {
        "operationName": "recentAcSubmissionList",
        "query": """
         query recentAcSubmissionList($username: String!, $limit: Int!) {
            recentAcSubmissionList(username: $username, limit: $limit) {
                id
                title
                titleSlug
                timestamp
                lang
                statusDisplay
                runtime
                memory
            }
        }
        """,
        "variables": {
            "username": username,
            "limit": limit
        }
    }
    
    response = requests.post(url, headers=headers, cookies=cookies, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        # Check for the expected key
        if 'data' in data and 'recentAcSubmissionList' in data['data']:
            return data['data']['recentAcSubmissionList']
        else:
            print(f"Error: Unexpected response format. {data}")
            return None
    else:
        print(f'Failed to retrieve submissions for {username}: {response.status_code}')
        return None



def main():
    with open('usernames.txt', 'r') as file:
        usernames = file.readlines()
    
    usernames = [username.strip() for username in usernames if username.strip()]

    df_all = pd.read_csv('recent_ac_submissions.csv') if pd.io.common.file_exists('recent_ac_submissions.csv') else pd.DataFrame()

    for username in usernames:
        recent_subs = get_recent_ac_submissions(username)
        df = pd.DataFrame(recent_subs)
        print(len(df))
        df['username'] = username
        df_all = pd.concat([df_all, df], ignore_index=True)


    df_all['runtime_val'] = df_all['runtime'].apply(lambda x: int(x.split()[0]))
    df_all['memory_val'] = df_all['memory'].apply(lambda x: float(x.split()[0]))
    df_all.sort_values(by=['username', 'titleSlug', 'runtime_val', 'memory_val'], ascending=[True, True , True, True], inplace=True)
    df_all = df_all.drop_duplicates(subset=['username', 'titleSlug'], keep='first')
    df_all['overall_score'] = df_all['runtime_val'] + df_all['memory_val']

    df_overall_rank = df_all.groupby('username')['overall_score'].sum().reset_index().sort_values(by='overall_score')

    #print(df_overall_rank)

    df_all.to_csv('recent_ac_submissions.csv', index=False)
    df_overall_rank.to_csv('overall_leaderboard.csv', index=False)

    print("successfully scraped and saved data!")

if __name__ == "__main__":
    main()
