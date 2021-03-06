import sys
from os import path

import json
import psycopg2
import person_generator

basepath = path.dirname(__file__)
try:

    filepath = path.abspath(path.join(basepath, "..",  "secrets.json"))
    secrets = json.load(open(filepath, "r"))
except:
    print('secrets file not found')
    quit

print('Connecting to host: "' + secrets['pgHost'] + '", database: "' +
      secrets['pgDatabase'] + '" as user "' + secrets['pgUsername'] + '"')

connection = psycopg2.connect(host=secrets['pgHost'], database=secrets['pgDatabase'],
                              user=secrets['pgUsername'], password=secrets['pgPassword'])
cur = connection.cursor()


print('Dropping tables if they exist')
dropSql = open(path.abspath(
    path.join(basepath, "..", "scripts", 'drop_tables.sql')))
cur.execute(dropSql.read())
connection.commit()

print('Creating the tables')
createSql = open(path.abspath(
    path.join(basepath, "..", "scripts", 'create_tables.sql')))
cur.execute(createSql.read())
connection.commit()

# seed the tables with data

# batch insert

maleNames = open(path.abspath(path.join(basepath, "..", "data",
                                        'first_names_male.csv'))).read().splitlines()
femaleNames = open(path.abspath(path.join(
    basepath, "..", "data", 'first_names_female.csv'))).read().splitlines()
lastNames = open(path.abspath(
    path.join(basepath, "..", "data", 'last_names.csv'))).read().splitlines()

cityNames = open(path.abspath(
    path.join(basepath, "..", "data", 'city_names.csv'))).read().splitlines()

streetSuffixes = open(path.abspath(
    path.join(basepath, "..", "data", 'street_suffixes.csv'))).read().splitlines()

stateCodes = open(path.abspath(
    path.join(basepath, "..", "data", 'state_codes.csv'))).read().splitlines()

values = []


quantity = 500000
ssnStart = 123456789
ssnEnd = ssnStart + quantity
socialSecurityNumbers = list(range(ssnStart, ssnEnd))
print('Generating ' + str(ssnEnd - ssnStart) + " records...")

insertBatchSize = 1000

for p in person_generator.generate(socialSecurityNumbers, femaleNames, maleNames, lastNames, cityNames, streetSuffixes, stateCodes):
    values.append("('%s', '%s', '%s', '%s', '%s', '%s', '%s','%s', %d, '%s')" % (
                  p['ssn'],
                  p['firstName'].replace("'", "''"),
                  p['lastName'].replace("'", "''"),
                  p['sex'],
                  p['street'].replace("'", "''"),
                  p['city'].replace("'", "''"),
                  p['state'],
                  p['zip'],
                  p['netWorth'],
                  p['generated_timestamp'])
                  )
    if (len(values) == insertBatchSize):
        print("inserting " + str(insertBatchSize))
        insertSql = "INSERT INTO person (ssn, first_name, last_name, sex_code, street_address, city_name, state_code, zip, net_worth_amount, generated_timestamp) VALUES" + ",".join(values)
        cur.execute(insertSql)
        connection.commit()
        values.clear()

if(len(values) > 0):
    print("inserting " + str(len(values)))
    insertSql = "INSERT INTO person (ssn, first_name, last_name, sex_code, street_address, city_name, state_code, zip, net_worth_amount, generated_timestamp) VALUES" + ",".join(values)
    cur.execute(insertSql)
    connection.commit()

createSql = open(path.abspath(
    path.join(basepath, "..", "scripts", 'speed_statistics.sql')))
cur.execute(createSql.read())
results = cur.fetchone()

observationFile = open(path.abspath(
    path.join(basepath, "..", 'observations.md')), "a")
pythonVer = "Python %d.%d.%d" % (
    sys.version_info.major, sys.version_info.minor, sys.version_info.micro)
observationFile.write("|%s|%s|%s|%s|%s|\n" % (str(results[0]),
                                              str(results[1]),
                                              str(results[2]),
                                              pythonVer,
                                              str(results[3])))
connection.close()
