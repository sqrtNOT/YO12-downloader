#!/usr/bin/python3
import requests
from requests.adapters import HTTPAdapter, Retry
from bs4 import BeautifulSoup
import os
import time
import re
import pyexiv2

# output_directory is where the image files will be saved
output_directory = ""
# log file is where any failed downloads, corrupt images, etc. will be written
logfile = open("", 'w')
# how long to wait between each request in seconds
wait_time = 10

if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# ukiyo-e.org isn't perfectly stable so we need to use retries so it won't crash midway
sess = requests.Session()
retries = Retry(total=10, backoff_factor=10)
sess.mount('https://', HTTPAdapter(max_retries=retries))

top_url = "https://ukiyo-e.org"
top_page = requests.get(top_url, timeout=10)
top_soup = BeautifulSoup(top_page.text, 'html.parser')
artist_pages = [{'artist_name': x['title'], 'artist_url': x['href']} for x in top_soup.find_all('a', class_="artist")]

for artist in artist_pages:
    # create a folder for each artist individual in the dataset
    artist_path = (os.path.join(output_directory, artist['artist_name']))
    if not os.path.exists(artist_path):
        os.makedirs(artist_path)

    print(f"throttling for {wait_time} seconds before grabbing first artist page")
    time.sleep(wait_time)

    artist_page = requests.get(artist['artist_url'], timeout=10)
    artist_soup = BeautifulSoup(artist_page.text, 'html.parser')
    prints = []
    soups = []
    soups.append(artist_soup)


    # Handle pagination because only 100 prints are displayed at a time
    try:
        print_count = int("".join([_ for _ in artist_soup.find('strong').text if _ in "0123456789"]))
    except:
        logfile.write(f"failed to get print count for {artist}\n")
        print_count = 0
    if print_count > 100:
        for i in range(1, print_count//100+1):
            print(f"throttling for {wait_time} seconds before grabbing extra artist pages")
            time.sleep(wait_time)

            start = i*100
            artist_page = requests.get(artist['artist_url']+f"?start={start}", timeout=10)
            artist_soup = BeautifulSoup(artist_page.text, 'html.parser')
            soups.append(artist_soup)

    # iterate over each artist page to get a list of individual works
    for soup in soups:
        for div in soup.find_all('div', class_='img col-xs-6 col-sm-4 col-md-3'):
            try:
                print_url = div.find('a')['href']
                print_metadata = artist.copy()
                print_metadata['print_url'] = print_url
                print_metadata['artist_path'] = artist_path+'/'
                prints.append(print_metadata)
            except:
                logfile.write(f"{div} failed while extracting div from {artist}\n")

    # each print has its own page with metadata and a link to the full res image
    for work in prints:
        print(f"throttling for {wait_time} seconds before grabbing print page")
        time.sleep(wait_time)

        print_page = requests.get(work['print_url'], timeout=10)
        print_soup = BeautifulSoup(print_page.text, 'html.parser')

        metadata = print_soup.find('div', class_='details')
        if metadata:
            text_metadata = re.sub(r"\t+", ' ', re.sub(r"\s+", ' ', metadata.text)).strip()
        else:
            # no metadata so no download link
            continue

        image_search = metadata.find('a', class_='btn', href=True)
        if image_search:
            image_url = image_search['href']
            try:
                image_extension = image_url.split('.')[-1]
            except:
                image_extension = ""
        else:
            # no image just skip
            continue

        # description is the main with title as the fallback
        description_search = re.search(r'Description\s*:([\s\S]+?)(Download Image|$)', text_metadata, re.IGNORECASE)
        title_search = re.search(r'Title\s*:([\s\S]+?)(?:[\S]+?:)', text_metadata, re.IGNORECASE)

        description = ""
        if description_search:
            description = description_search.group(1).strip()
        elif title_search:
            description = title_search.group(1).strip()

        # dates are in an extremely inconsistent format so we just grab it all
        date_search = re.search(r'Date\s*:([\s\S]+?)(?:[\S]+?:)', text_metadata, re.IGNORECASE)
        date = ""
        if date_search:
            date = date_search.group(1).strip()
        description = f"{work['artist_name']}, {description}, {date}".strip(', ')

        # download image and save with metadata added to the exif tags
        filename = "_".join(work['print_url'].split('/')[-2:])
        filepath = work['artist_path'] + filename + "." + image_extension

        print(f"throttling for {wait_time} seconds before grabbing image: {filepath}")
        time.sleep(wait_time)

        image_response = requests.get(image_url, timeout=10)
        if image_response:
            try:
                image = pyexiv2.ImageData(image_response.content)
            except:
                # no image content
                logfile.write(f"{image_url} contains no content\n")
                continue
        else:
            logfile.write(f"{image_url} did not resolve\n")

        # if something isn't jpeg or png then writing the exif data will fail
        try:
            image.clear_exif()
            image.modify_exif({'Exif.Image.ImageDescription': description,
                               'Exif.Image.Artist': work['artist_name']})
        except:
            logfile.write(f"{filename} has no exif capability\n")
        # write file to disk
        with open(filepath, 'wb') as outfile:
            outfile.write(image.get_bytes())

logfile.close()
