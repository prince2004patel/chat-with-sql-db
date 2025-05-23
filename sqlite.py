import sqlite3

# connect to sqllite
connection = sqlite3.connect("student.db")

# create a cursor object to insert record, create table
cursor = connection.cursor()

# create the table
table_info = """
create table STUDENT(NAME VARCHAR(25),
CLASS VARCHAR(25), SECTION VARCHAR(25), MARKS INT)
"""

cursor.execute(table_info)

# insert some records
cursor.execute(''' Insert Into STUDENT values('Prince','Data Science','A',90)''')
cursor.execute(''' Insert Into STUDENT values('Nakul','Data Science','A',100)''')
cursor.execute(''' Insert Into STUDENT values('Param','Web Developer','B',95)''')
cursor.execute(''' Insert Into STUDENT values('Purv','Web Developer','B',90)''')
cursor.execute(''' Insert Into STUDENT values('Xyz','Software Developer','C',85)''')

# display all records
print("the inserted records are")
data = cursor.execute('''Select * from STUDENT''')
for row in data:
    print(row)

# commit your changes in the database
connection.commit()
connection.close()