#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Author: abhiigatty@gmail.com 
    Feel free to reuse the code just don't blame me
    and support Anime artist by purchasing their merch and swags """

import requests, json, validators, re
from clint.textui import colored
from pathlib import Path
from tqdm import tqdm 
from multiprocessing.dummy import Pool as ThreadPool
from Crypto.Cipher import AES
from prettytable import PrettyTable
from download import download_from_url


""" Function to delete a directory """
def delete_directory(directory_path) :
    if directory_path.exists():
        for sub in directory_path.iterdir() :
            if sub.is_dir() :
                delete_directory(sub)
            else :
                sub.unlink()
        directory_path.rmdir()
    
""" Function used to decrypt the cipher using a key"""
def decrypt_text(secret_key):
    # URL encrypted to bytes-string with a secret key
    cipher_url = b'An\xc77>^(\x00a\xbb\xde6O\xf1syh\xb6\xab\x9c\x94CF\xff\x8f\xb8}\xc5\x81Q8\xafd\x81$\x90\xe5\xbeM"\xbdO\xdff\xd7\xf23\xe4'    
    try:
        # Creating an object to use decrypt method
        lock_obj = AES.new(secret_key, AES.MODE_CFB, "is a 16 byte key")
        # URL decrypted and convert to string
        plain_url = str(lock_obj.decrypt(cipher_url), "utf-8")
        return plain_url
    except:
        return "invalid key"

""" Function for a 'yes or no' option selector """
def yes_or_no(question): # Include '?' in the question string
    # Input returns the empty string for "enter"
    yes = ('yes','y', 'ye', '')
    no = ('no','n')
    # Input choice
    choice = input(question + colored.green(" [Y]") + "es or " + colored.red("[N]") + "o: ").lower()
    while True:
        # If choice not either yes or no then ask input again
        if choice not in yes + no:
            choice = input("Please Choose " + colored.green("[Y]") + "es or " + colored.red("[N]") + "o: ").lower()
            continue
        if choice in yes: 
            return True
        elif choice in no:
            return False

""" Function to get a web page content """
def download_data(url):
    try:
        print(">> "+colored.cyan("Downloading data...")+": "+colored.yellow(url))
        data = requests.get(url)
        return data
    except requests.exceptions.RequestException as err:
        print(err)
        return "invalid"

""" Function to download and save json data in a file """
def url_to_json(data_url, directory_path="."):
    data = download_data(data_url)
    try:
        data_from_json = data.json()
        file_name = Path(data_url).parts[-1]
        file_path = directory_path / file_name
        with file_path.open(mode="w", encoding ="utf-8") as fh:
            json.dump(data_from_json, fh, indent=4)
        print(">> "+colored.cyan("Written to file")+": "+colored.green(file_path))
        return file_name
    except ValueError:
        print("URL file not in json format!")
        exit()
        
""" Prepare the multiple-parameters for multiprocessing """
def multi_run_wrapper(args):
   return get_anime_episode_urls(*args)

""" Gets the media download url """
def get_anime_episode_urls(url, data):
    links = requests.post(url, data=data) 
    try:
        links = list(links.json().values())
        while "none" in links: links.remove("none")
        resp_url = links[0]
        episode_download_url = resp_url
        # Grab redirect url if it exists
        try:
            redirect_message = ""
            redirected_url = requests.head(resp_url).headers
            if 'Location' in redirected_url:
                episode_download_url = redirected_url['Location']
                redirect_message = " -> " + colored.green("Redirect") + ": " + episode_download_url 
        except:
            pass
        print(">> " + colored.yellow("URL") + ": " + resp_url + redirect_message)
        return episode_download_url
    except:
        print("Failed: {}".format(data))

""" Gets the animes urls and saves it """
def getAnime(main_url):
    file_details = {}
    main_data = download_data(main_url).json()[0] # Get json data and convert returned data to dict from list

    # Create the directory if it does not exist
    dir_name  = "getanime_temp_json"
    Path(dir_name).mkdir(exist_ok=True)  
    directory_path = Path(dir_name)

    print("=> "+colored.cyan("Fetching Database, Please wait...."))
    # Download the json files 
    for key, value in main_data.items():
        # Ignore other files for downloading
        if Path(value).suffix == ".php": # The php file url is required for fetching further information
            php_url = value
            print(">> "+colored.cyan("DRIVER_URL")+": "+colored.green(value))
            continue
        if validators.url(value): # If url is invalid then do nothing otherwise process it
            file_name = url_to_json(value, directory_path)  
            file_size = (directory_path / file_name).stat().st_size   # Get file size in bytes
            file_details[file_name] = file_size   # Create a dict of file_name and it"s size
        else:
            pass
    
    json_file_name = max(file_details, key=file_details.get)  # We"ll use the json file with max size
    file_path = directory_path / json_file_name  # Build the path of the json file

    # Load json file contents into a dict for faster access
    with file_path.open(mode="r", encoding ="utf-8") as fh:  # Load json from file
        anime_details = json.load(fh)
    anime_names = []
    for anime in anime_details:
        anime_names.append(anime["Title"])
    print(">> No. of animes found: ",len(anime_names))
    
    # Loop until user wants to stop
    while True:
        # Loop until a valid anime title is found
        anime_to_download = input(">> "+colored.cyan(colored.cyan("Enter Anime Title or [quit]"))+": ")
        if anime_to_download in ["quit","q","exit"]:
            return
        print(colored.red("Searching Keyword: ") + colored.yellow(anime_to_download))
        regex = re.compile(".*"+anime_to_download+".*", re.IGNORECASE) # Create the regular expression to find the string
        list_of_result = list(filter(regex.match, anime_names))
        
        # Start loop again if no animes found
        if len(list_of_result) is 0:
            print("=> "+colored.red("No match found! ")+colored.cyan("Try another title"))
            continue

        # Display the anime titles to choose from in a table
        table = PrettyTable(['No.', 'Title'])
        anime_list = {}
        for pos, anime_name in enumerate(list_of_result, start=1):
            table.add_row([pos, anime_name])
            anime_list[pos] = anime_name
        table.add_row([pos+1, "<<< Exit <<<"])
        print(table)

        while True:
            choice = int(input(">> "+colored.cyan("Choose a number")+": "))
            if anime_list[choice] == "<<< Exit <<<":
                return
            elif choice in anime_list.keys():
                anime_choice = anime_list[int(choice)]
                break
            else:
                print(colored.red("Error")+": "+colored.cyan("Invalid! ")+"Please Try Again!")

        # Find the anime download page link
        for anime in anime_details:
            if anime["Title"] is anime_choice:
                download_link = anime["Link"]
                break
        print(">> "+colored.cyan("Anime Page: "+colored.yellow(download_link)))
        
        # Find details about anime and download links to each episode
        data = {}
        data["Episodes"] = download_link
        reply = requests.post(php_url, data=data)
        animes_epi_links = reply.json()["episodes"]
        no_of_episodes = len(animes_epi_links)
        print(colored.cyan(anime_choice)+colored.cyan(" has ")+colored.green(no_of_episodes)+colored.cyan(" episodes"))
        
        # Find the find anime media download links
        list_of_data = []
        final_links_list = []
        for anime in animes_epi_links:
            data = {}
            data["LinkIos"] = anime["href"]
            list_of_data.append((php_url, data))


        # Make the Pool of workers for multiprocessing
        # thread_count = int(no_of_episodes/2)
        pool = ThreadPool(25) 
        # Open the urls in their own threads and return the results
        final_links_list = pool.map(multi_run_wrapper, list_of_data)
        # close the pool and wait for the work to finish 
        pool.close() 
        pool.join()

        # Create the directory if it does not exist
        dir_name  = "getanime_links"
        Path(dir_name).mkdir(exist_ok=True)  
        directory_path = Path(dir_name)

        # Create a file with all the links
        final_anime_title = str(anime_choice.replace(" ","_")
        file_name = final_anime_title + "_getanime.txt"
        file_path = directory_path / file_name
        with file_path.open(mode="w", encoding ="utf-8") as fh:
            fh.write("\n".join(final_links_list))
        print("=> "+colored.cyan("File created: ")+colored.green(file_name))

        # Ask if user wants to download the series
        if yes_or_no(question="\nDownload all the episodes?"):
            for episode_url in final_links_list:
                download_from_url(episode_url, fina_anime_title)

        # Ask if user wants to run again
        if yes_or_no(question="\nFind another anime?"):
            pass
        else:
            return

""" Main function that checks the key and removes temp dirs """
def main():
    
    try:
        secret_key = str(input("Enter Secret Key: ")).lower()
        project_url = decrypt_text(secret_key)
        # Check if the decrypted url is in a valid url structure
        if validators.url(project_url):
            print(colored.green("Welcome, glad to have you back!"))
            getAnime(main_url=project_url)
        else:
            print(colored.red("Error: ")+colored.cyan("Have a nice day!"))
    except:
        # Is executed if the getAnime function has some problems in it
        print(colored.red("Error: ")+colored.yellow("You tried something weird, Didn't you?! "))
    
    # Clean up the temp directories if created
    temp_dir = Path("getanime_temp_json")
    delete_directory(temp_dir)
    print("=> "+colored.cyan("GoodBye! "))

# Run the code below only if this is executed as a program and not imported as module
if __name__ == "__main__":
    main()
