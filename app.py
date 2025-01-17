from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

URLS = {
    "Egg Prices": "https://daatacenter.com/trade/today-egg-rate-bangalore/",
    "Chicken Rates": "https://daatacenter.com/chicken-rate/chicken-rate-today-in-bangalore/",
    "Vegetable Prices": "https://market.todaypricerates.com/Bengaluru-vegetables-price-in-Karnataka",
    "Petrol Prices": "https://www.ndtv.com/fuel-prices/petrol-price-in-bangalore-city",
    "Diesel Prices": "https://www.ndtv.com/fuel-prices/diesel-price-in-bangalore-city",
    "Fruit Prices": "https://market.todaypricerates.com/Karnataka-fruits-price",
    "Flower Rates": "https://daatacenter.com/flowers-price/today-flower-rate-in-bangalore-market/",
}

def scrape_table(url):
    """Scrape table or div data from the specified URL."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Special case for petrol and diesel prices with div id="myID"
        if "ndtv.com" in url:
            div = soup.find("div", id="myID")
            if div:
                rows = div.find_all("tr")
                if rows:
                    headers_row = rows[0]
                    table_headers = [cell.text.strip() for cell in headers_row.find_all(["th", "td"])]

                    # Remove "Change" column if it exists
                    if "Change" in table_headers:
                        change_index = table_headers.index("Change")
                        table_headers.pop(change_index)
                    else:
                        change_index = None

                    # Extract rows without "Change" column
                    table_rows = []
                    for row in rows[1:]:
                        cells = [cell.text.strip() for cell in row.find_all(["td", "th"])]
                        if change_index is not None and len(cells) > change_index:
                            cells.pop(change_index)
                        if any(cells):
                            table_rows.append(cells)

                    return table_headers, table_rows

                return "No table-like rows found in the div with id='myID'.", []

            return "No div with id='myID' found on the webpage.", []

        # Generic table scraping logic
        table = soup.find("table")
        if table:
            headers_row = table.find("tr")
            table_headers = [cell.text.strip() for cell in headers_row.find_all(["th", "td"])]

            table_rows = []
            for row in table.find_all("tr")[1:]:
                cells = [cell.text.strip() for cell in row.find_all(["td", "th"])]
                if any(cells):
                    table_rows.append(cells)

            return table_headers, table_rows

        return "No table found on the webpage.", []

    except requests.RequestException as e:
        return f"Failed to retrieve data: {str(e)}", []

@app.route("/", methods=["GET", "POST"])
def index():
    """Render the index page and handle form submissions."""
    selected_category = None
    table_headers = []
    table_rows = []
    error_message = None

    if request.method == "POST":
        selected_category = request.form.get("category")
        if selected_category in URLS:
            url = URLS[selected_category]
            result = scrape_table(url)

            if isinstance(result[0], str):  # Error occurred
                error_message = result[0]
            else:
                table_headers, table_rows = result

    return render_template(
        "index.html",
        categories=URLS.keys(),
        selected_category=selected_category,
        table_headers=table_headers,
        table_rows=table_rows,
        error_message=error_message,
    )

if __name__ == "__main__":
    app.run(debug=True)
