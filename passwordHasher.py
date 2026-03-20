import csv
import hashlib
import secrets

def generate_salt():
    return secrets.token_urlsafe(16)

input_file = 'dataset/Users.csv'
output_file = 'dataset/HashedUsers.csv'
with open(input_file) as csvfile:
    reader = csv.DictReader(csvfile)
    fieldnames = reader.fieldnames + ['salt']
    with open(output_file, mode='w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in reader:
            password = row['password'].strip()
            salt = generate_salt()
            password_and_salt = (password + salt).encode('utf-8')
            hashed_password = hashlib.sha256(password_and_salt).hexdigest()
            row['salt'] = salt
            row['password'] = hashed_password

            writer.writerow(row)
