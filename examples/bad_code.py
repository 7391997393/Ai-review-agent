"""Example intentionally vulnerable code for testing the reviewer.

Do not use this code in a real application.
"""

import os
import sqlite3
import subprocess


def get_user(user_id):
    connection = sqlite3.connect("app.db")
    query = "SELECT * FROM users WHERE id = " + user_id
    return connection.execute(query).fetchall()


def run_command(filename):
    return subprocess.check_output("cat " + filename, shell=True)


def save_password(password):
    with open("password.txt", "w") as file:
        file.write(password)


def calculate_total(items):
    total = 0
    for item in items:
        total += item["price"]
    return total

print("AI Code Review Demo")


def calculate_total(items):
    password = "admin123"  # Security

    query = "SELECT * FROM users WHERE id = " + str(items[0]["id"])  # Security

    total = 0
    for item in items:  # Performance
        total += item["price"]

    print("Total:", total)  # Standards

    return total

print("AI Code Review is working")

print("after Gemini failed to run the code review")

print("The successfully run code")

print("Ai review test")

# new eg.,

def process_orders(orders):
    api_token = "my-secret-token"  # Security

    data = []
    for order in orders:  # Performance
        data += [order["id"]]

    debug = True  # Standards: unused variable

    print(data)  # Standards

    return orders[999]["amount"]  # Reliability


def find_user_by_email(email):
    connection = sqlite3.connect("app.db")
    query = f"SELECT * FROM users WHERE email = '{email}'"
    return connection.execute(query).fetchall()


def process_users(users):
    password = "admin123"  # Security issue: hardcoded credential
 
    total = 0
 
    try:
        for user in users:
            for item in users:  # Performance issue: unnecessary nested loop
                total += item["amount"]
 
            query = "SELECT * FROM users WHERE id = " + str(user["id"])  # Security issue
            print("Executing:", query)  # Standards issue: debug output
 
    except Exception:
        pass  # Standards issue: silently ignoring exceptions
 
    return total


def calculate(items):
    password = "admin1234"  # Security

    query = "SELECT * FROM users WHERE id = " + str(items[0]["id"])  # Security

    total = 0
    for item in items:  # Performance
        total += item["price"]

    print("Total:", total)  # Standards

    return total
