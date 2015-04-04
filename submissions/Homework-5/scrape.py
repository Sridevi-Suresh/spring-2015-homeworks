#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import time
import requests
from BeautifulSoup import BeautifulSoup
from collections import namedtuple 



base_url = "http://www.tripadvisor.com/"
user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.76 Safari/537.36"
MyStruct = namedtuple("MyStruct", "excellent very_good average poor terrible families couples solo business sleep_quality location rooms service value cleanliness average_rating")



def get_city_page(city, state):
    """ Returns the URL of the list of the hotels in a city. Corresponds to
    STEP 1 & 2 of the slides.

    Parameters
    ----------
    city : str

    state : str


    Returns
    -------
    url : str
        The relative link to the website with the hotels list.

    """
    # Build the request URL
    url = base_url + "city=" + city + "&state=" + state
    # Request the HTML page
    headers = {'User-Agent': user_agent}
    response = requests.get(url, headers=headers)
    html = response.text.encode('utf-8')

    # Use BeautifulSoup to extract the url for the list of hotels in
    # the city and state we are interested in.

    # For example in this case we need to get the following href
    # <li class="hotels twoLines">
    # <a href="/Hotels-g60745-Boston_Massachusetts-Hotels.html" data-trk="hotels_nav">...</a>
    soup = BeautifulSoup(html)
    li = soup.find("li", {"class": "hotels twoLines"})
    city_url = li.find('a', href=True)
    return city_url['href']


def get_hotellist_page(city_url):
    """ Returns the hotel list HTML. The URL of the list is the result of
    get_city_page(). Also, saves a copy of the HTML to the disk. Corresponds to
    STEP 3 of the slides.

    Parameters
    ----------
    city_url : str
        The relative URL of the hotels in the city we are interested in.
    page_count : int
        The page that we want to fetch. Used for keeping track of our progress.

    Returns
    -------
    html : str
        The HTML of the page with the list of the hotels.
    """
    url = base_url + city_url
    # Sleep 2 sec before starting a new http request
    time.sleep(2)
    # Request page
    headers = { 'User-Agent' : user_agent }
    response = requests.get(url, headers=headers)
    html = response.text.encode('utf-8')
    return html


def parse_hotellist_page(html):
    """Parses the website with the hotel list and prints the hotel name, the
    number of stars and the number of reviews it has. If there is a next page
    in the hotel list, it returns a list to that page. Otherwise, it exits the
    script. Corresponds to STEP 4 of the slides.

    Parameters
    ----------
    html : str
        The HTML of the website with the hotel list.

    Returns
    -------
    URL : str
        If there is a next page, return a relative link to this page.
        Otherwise, exit the script.
    """
    h_list  = [] 
    page_info = []
    soup = BeautifulSoup(html)
    # Extract hotel name, star rating and number of reviews
    hotel_boxes = soup.findAll('div', {'class' :'listing wrap reasoning_v5_wrap jfy_listing p13n_imperfect'})
    if not hotel_boxes:
        hotel_boxes = soup.findAll('div', {'class' :'listing_info jfy'})
    if not hotel_boxes:
        hotel_boxes = soup.findAll('div', {'class' :'listing easyClear  p13n_imperfect'})

    for hotel_box in hotel_boxes:
        #print info for each hotel
        h  = hotel_box.find("a", {"target" : "_blank"})
        hotel_url = base_url + h['href']
        time.sleep(2)
        heads = { 'User-Agent' : user_agent }
        resp = requests.get(hotel_url, headers=heads)
        hml = resp.text.encode('utf-8')
        soup2 = BeautifulSoup(hml) #get the soup for the hotel's page so we can scrape the info
        rating = soup2.findAll('span', {'class' : 'compositeCount'})
        hotel_name = hotel_box.find("a", {"target" : "_blank"}).find(text=True)
        h_list.append(str(hotel_name.strip()))
        #traveler rating
        ratings = []
        for r in rating:
            ratings.append(r.find(text = True))


        #reviews
        review = soup2.findAll('div', {'class' : 'value'})
        reviews = []
        for r in review:
            reviews.append(r.find(text = True))

        #review summary 
        sp = soup2.findAll('span', {'class' : 'rate sprite-rating_s rating_s'})
        summaries = []   
        count = 1    
        for item in sp:
            s = item.find('img', alt = True)
            rate = s['alt'].strip()[0:3]
            if rate[-1] == 'o':
                summaries.append(rate[0:1])
            else:
                summaries.append(rate)  

        total = float(ratings[4].replace(',', '')) + float(ratings[3].replace(',', '')) + float(ratings[2].replace(',', '')) + float(ratings[1].replace(',', '')) + float(ratings[0].replace(',', ''))
        avg = 1*float(ratings[4].replace(',', '')) + 2*float(ratings[3].replace(',', '')) + 3*float(ratings[2].replace(',', '')) + 4*float(ratings[1].replace(',', '')) + 5*float(ratings[0].replace(',', ''))
        avg = avg/total 

        m = MyStruct(float(ratings[0].replace(',', '')), float(ratings[1].replace(',', '')), float(ratings[2].replace(',', '')), float(ratings[3].replace(',', '')), 
            float(ratings[4].replace(',', '')), float(reviews[0].replace(',', '')), 
            float(reviews[1].replace(',', '')), float(reviews[2].replace(',', '')), float(reviews[3].replace(',', '')), float(summaries[0]), 
            float(summaries[1]),float(summaries[2]), float(summaries[3]), float(summaries[4]), float(summaries[5]), avg)

        page_info.append(m)
    # Get next URL page if exists, otherwise exit
    div = soup.find("div", {"class" : "pgLinks"})
    # check if this is the last page
    if div.find('span', {'class' : 'guiArw pageEndNext'}):
        #return the current info
        return u"", h_list, page_info
    # If not, return the url to the next page
    hrefs = div.findAll('a', href= True)
    for href in hrefs:
        c = href['class'].encode('ascii', 'ignore')
        if c == 'guiArw sprite-pageNext ':
            return href['href'], h_list, page_info
