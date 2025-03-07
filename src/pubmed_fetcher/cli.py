import argparse
from fetcher import fetch_pubmed_papers, save_to_csv

def main():
    parser = argparse.ArgumentParser(description="Fetch PubMed papers based on query.")

    parser.add_argument("query", type=str, help="Search query for PubMed API")
    parser.add_argument("-f", "--file", type=str, default="output.csv", help="Output file name")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    print(f"Fetching papers for query: {args.query}...")
    papers = fetch_pubmed_papers(args.query)

    if args.debug:
        print("Fetched Papers:", papers)

    if papers:
        save_to_csv(papers, args.file)
    else:
        print("No relevant papers found.")

if __name__ == "__main__":
    main()
