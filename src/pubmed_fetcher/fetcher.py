import requests
import csv
import xmltodict
from urllib.parse import urlencode
from typing import List, Dict

# Base URL for PubMed API
BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

def fetch_pubmed_papers(query: str, max_results: int = 50) -> List[Dict]:
    """
    Fetch papers from PubMed API using the given query.
    """
    search_params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json"
    }
    
    search_url = BASE_URL + "esearch.fcgi?" + urlencode(search_params)
    search_response = requests.get(search_url).json()
    
    # Extract paper IDs
    paper_ids = search_response.get("esearchresult", {}).get("idlist", [])
    
    if not paper_ids:
        print("No papers found for the given query.")
        return []

    # Fetch details for the retrieved paper IDs
    fetch_params = {
        "db": "pubmed",
        "id": ",".join(paper_ids),
        "retmode": "xml"
    }

    fetch_url = BASE_URL + "efetch.fcgi?" + urlencode(fetch_params)
    fetch_response = requests.get(fetch_url)
    
    # Parse XML response
    papers_data = xmltodict.parse(fetch_response.content)
    
    return process_papers(papers_data)

def process_papers(papers_data) -> List[Dict]:
    """
    Process the raw XML data and extract relevant details.
    """
    papers_list = []
    
    articles = papers_data.get("PubmedArticleSet", {}).get("PubmedArticle", [])
    if not isinstance(articles, list):
        articles = [articles]

    for article in articles:
        paper_info = extract_paper_info(article)
        if paper_info:
            papers_list.append(paper_info)

    return papers_list

def extract_paper_info(article) -> Dict:
    """
    Extracts required details from a single PubMed article.
    """
    try:
        article_info = article["MedlineCitation"]["Article"]
        pubmed_id = article["MedlineCitation"]["PMID"]["#text"]
        title = article_info["ArticleTitle"]
        pub_date = article_info.get("Journal", {}).get("JournalIssue", {}).get("PubDate", {}).get("Year", "Unknown")
        
        authors_list = article_info.get("AuthorList", {}).get("Author", [])
        if not isinstance(authors_list, list):
            authors_list = [authors_list]

        non_academic_authors = []
        company_affiliations = []
        corresponding_email = ""

        for author in authors_list:
            affiliation_info = author.get("AffiliationInfo", {})
            if not affiliation_info:
                continue

            affiliation_text = affiliation_info.get("Affiliation", "")
            
            # Check for non-academic institutions
            if any(keyword in affiliation_text.lower() for keyword in ["pharma", "biotech", "inc", "ltd", "corp"]):
                non_academic_authors.append(author.get("LastName", "") + " " + author.get("ForeName", ""))
                company_affiliations.append(affiliation_text)

            # Extract corresponding author email
            if "@" in affiliation_text:
                corresponding_email = affiliation_text.split()[-1]

        if non_academic_authors:
            return {
                "PubmedID": pubmed_id,
                "Title": title,
                "Publication Date": pub_date,
                "Non-academic Author(s)": ", ".join(non_academic_authors),
                "Company Affiliation(s)": ", ".join(company_affiliations),
                "Corresponding Author Email": corresponding_email
            }

    except Exception as e:
        print(f"Error processing article: {e}")
    
    return None

def save_to_csv(papers: List[Dict], filename: str):
    """
    Saves the list of papers to a CSV file.
    """
    if not papers:
        print("No data to save.")
        return

    headers = ["PubmedID", "Title", "Publication Date", "Non-academic Author(s)", "Company Affiliation(s)", "Corresponding Author Email"]

    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(papers)

    print(f"Data successfully saved to {filename}")
