import csv
def clean_value(value):
    """cleans the price by deleting the 7 symbol and ',' """
    if not value:
        return "0.0"
    clean_str = value.strip().replace('$', '').replace(',', '')
    return str(float(clean_str))

input_file = 'dataset/Auction_Listings.csv'
output_file = 'dataset/Clean_Auction_listing.csv'
with open(input_file) as csvfile:
    reader = csv.DictReader(csvfile)
    fieldnames = reader.fieldnames + ['salt']
    with open(output_file, mode='w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in reader:
            row['Reserve_Price'] = clean_value(row['Reserve_Price'])
            writer.writerow(row)
