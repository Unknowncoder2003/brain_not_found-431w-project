import csv
import hashlib
import secrets

def generate_salt():
    return secrets.token_urlsafe(16)
def hash_with_salt(password, salt):
    password_and_hash = password + salt
    return hashlib.sha256(password_and_hash.encode('utf-8')).hexdigest()
input_file = 'dataset/Users.csv'
output_file = 'dataset/HashedUsers.csv'
with open(input_file) as csvfile:
    reader = csv.DictReader(csvfile)
    fieldnames = reader.fieldnames + ['salt']
    with open(output_file, mode='w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in reader:
            salt = generate_salt()
            row['salt'] = salt
            row['password'] = hash_with_salt(row['password'], salt)
            writer.writerow(row)
