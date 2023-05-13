#!/bin/bash
set -e

# Get the CSRF token by scraping the login form page
csrf_token=$(curl -c cookies.txt http://localhost/login | grep csrf_token | sed 's/.*value="\([^"]*\)".*/\1/')

# Test the login endpoint with correct credentials

response=$(curl -b cookies.txt -X POST -d "email=lhhung@uw.edu&password=qwerty&csrf_token=${csrf_token}" http://localhost/login | sed -n 's:.*<title>\(.*\)<\/title>.*:\1:p')
if [ "$response" != "Redirecting..." ]; then
    echo "$response"
    echo "Login endpoint failed with correct credentials"
    exit 1
fi
response=$(curl -b cookies.txt -X POST -d "email=wrong@uw.edu&password=qwerty&csrf_token=${csrf_token}" http://localhost/login | sed -n 's:.*<title>\(.*\)<\/title>.*:\1:p')
if [ "$response" != "Login" ]; then
    echo "Login endpoint failed with incorrect credentials"
    exit 1
fi
echo "Login endpoint passed with both correct and incorrect credentials"
