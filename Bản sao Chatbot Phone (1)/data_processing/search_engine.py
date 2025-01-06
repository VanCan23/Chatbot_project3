import requests
from data_processing.llm_prompting import summarize_content
from data_processing.web_scraper import retrieve_content

def search(search_item, api_key, cse_id, search_depth=10, site_filter=None):
    service_url = 'https://www.googleapis.com/customsearch/v1'

    params = {
        'q': search_item,
        'key': api_key,
        'cx': cse_id,
        'num': search_depth
    }

    try:
        response = requests.get(service_url, params=params)
        response.raise_for_status()
        results = response.json()

        if 'items' in results:
            if site_filter is not None:
                filtered_results = [result for result in results['items'] if site_filter in result['link']]
                if filtered_results:
                    return filtered_results
                else:
                    print(f"No results with {site_filter} found.")
                    return []
            else:
                if 'items' in results:
                    return results['items']
                else:
                    print("No search results found.")
                    return []

    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the search: {e}")
        return []
  
    
TRUNCATE_SCRAPED_TEXT = 50000
def get_search_results(search_items, search_term, character_limit=500):
    results_list = []
    for idx, item in enumerate(search_items, start=1):
        url = item.get('link')
        snippet = item.get('snippet', '')
        web_content = retrieve_content(url, TRUNCATE_SCRAPED_TEXT)

        if web_content is None:
            print(f"Error: skipped URL: {url}")
        else:
            summary = summarize_content(web_content, search_term, character_limit)
            result_dict = {
                'id': idx,
                'url': url,
                'title': snippet,
                'summary': summary
            }
            results_list.append(result_dict)
    return results_list