#!/usr/bin/python2.7 -tt
"""This code analizes Google Analytics data"""
##Import libraries
import pandas as pd
import re
import urllib
import html2text
import requests
import time
import os.path

##Read Google Analytics file to be analyzed
##file=raw_input("Enter Google Analytics file name: ")
FILE_NAME = 'Analytics DataScienceCentral.com Pages 20110901-20150331_10000.csv'
GA_NEW = pd.read_csv(FILE_NAME, skiprows=6, nrows=6845, thousands=',')

##Read previous OUTPUT file
OUTPUT = raw_input("Enter previous OUTPUT file: ")
if os.path.isfile(OUTPUT):
    OLD_DATA = pd.read_csv(OUTPUT)
OLD_PAGE = OLD_DATA['Page'].astype(str).values

##Read previous input file (help to do not process twice old data)
FILE_OLD = 'Analytics DataScienceCentral.com Pages 20110901-20150228_10000.csv'
GA_OLD = pd.read_csv(FILE_OLD, skiprows=6, nrows=6400, thousands=',')

## Initializing new columns and variables
GA_NEW['mobile'] = 0
GA_NEW['TimeSensitive'] = 0
GA_NEW['Thereistitle'] = 0
GA_NEW['title'] = ''
GA_NEW['Date'] = ''
GA_NEW['exist'] = 0
GA_NEW['url'] = ""

MOBILE_INDEX = []

## This function return if page belongs to either DSC, AB , BDN or it does not exist.
## Create new column with values 1,2,3 or 0 respectively
def url_check(page):
    """This function check if page exists"""
    dsc_webpage = 'http://www.datasciencecentral.com'
    ab_webpage = 'http://www.analyticbridge.com'
    bdn_webpage = 'http://www.bigdatanews.com'
    url = dsc_webpage + page
    resp = requests.get(url)
    if resp.status_code < 400:
        number = 1
        checkurl = url
    else:
        url = ab_webpage + page
        resp = requests.get(url)
        if resp.status_code < 400:
            number = 2
            checkurl = url
        else:
            url = bdn_webpage+page
            resp = requests.get(url)
            if resp.status_code < 400:
                number = 3
                checkurl = url
            else:
                number = 0
                checkurl = ""
    return [number, checkurl]

## Function for extracting title and published date of Blog
def extract_title(url):
    """This function extracts the title from the webpage using regular expressions"""
    titlefile = urllib.urlopen(url)
    source_code = titlefile.read()
    titlefile.close()
    split_title = re.findall(r'<meta property="og:title" content="(.*?)" />', source_code)
    split_date = re.findall('</a><a class="nolink"> on (.*?)at', source_code)

    if len(split_title) != 0:
        thereis_title = 1
        title = html2text.html2text(''.join(split_title))
        title = title.replace('\n', '')
    else:
        thereis_title = 0
        title = ''

    if len(split_date) != 0:
        date = ''.join(split_date)
    else:
        date = ''

    return [thereis_title, title, date]

## Function evaluate if article could be time sensitive according list of words
def is_time_sensitive(title):
    """This function checks if title contains time senstive words"""
    count = 0
    number = 0
    timestop = ['weekly digest', 'webinar', 'conference', 'summit', 'upcoming']
    years = ['2010', '2011', '2012', '2013']
    months = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', \
    'september', 'october', 'november', 'december']
    timestop = timestop + months + years
    while number == 0 and count < len(timestop):
        if re.search(timestop[count], title.lower()) != None:
            number = 1
        count += 1
    return number

def populate_page(page, old):
    """This function checks if this webpage was previously analized"""
    if page in old:
        return [True, where(old == page)[0]]
    else:
        return [False, '']

## Main function
def main():
    """This is the main function"""
    page_num = 0
    count = 0
    list_page = GA_NEW['Page']

    for page in list_page:

        #Update old data with new data
        if populate_page(page, OLD_PAGE)[0]:
            ##print 'inside copying old data'
            ## Get index corresponding to old data
            page_index = populate_page(page, OLD_PAGE)[1][0]
            columns_tocopy = ['mobile', 'exist', 'TimeSensitive', 'Thereistitle', \
            'title', 'Date', 'exist', 'url']
            GA_NEW.ix[count, columns_tocopy] = OLD_DATA.ix[page_index, columns_tocopy]
            columns_toreplace = ['Pageviews', 'Unique Pageviews', 'Avg. Time on Page', \
            'Entrances', 'Bounce Rate', '% Exit', 'Page Value']
            GA_NEW.ix[count, columns_toreplace] = OLD_DATA.ix[page_index, \
            columns_toreplace]
            count += 1

        #Check if the web was analized and did not pass selection criteria, then do nothing
        elif page in GA_OLD['Page'].values:
            pass
        ## Populate new data
        else:
            ##Call function url_check(page) to check if page belongs to either DSC, AB,
            ##BDN or it does not exist. Create new column with values 1,2,3 or 0 respectively
            GA_NEW.ix[count, 'exist'] = url_check(page)[0]
            url = url_check(page)[1]
            GA_NEW.ix[count, 'url'] = url

            ##The following code analyzes if the page is mobile page and correct
            ##number of Pageviews, Unique Pageviews and Entrances from Desktop link
            stoppages = ['/jobs/search', '/m/404', '/m/signup', \
            '/m/signin?target=http://www.datasciencecentral.com/profiles/profile/'\
            'emailSettings?xg_source=msg_mes_network', \
            '/m/signup?target=/m&cancelUrl=/m', '/m/signin?target=/m&cancelUrl=/m', \
            '/jobs/search/results?page=2', '/forum?page=4', '/jobs/search/advanced', \
            '/profiles/blog/list?page=3', '/profiles/settings/editPassword', \
            '/main/invitation/new?xg_source=userbox', '/main/authorization/password'\
            'ResetSent?previousUrl=http://www.analyticbridge.com/main/authorization/'\
            'doSignIn?target=http://www.analyticbridge.com/', \
            '/profiles/friend/list?page=4', '/main/index/banned', \
            '/main/invitation/new?xg_source=empty_list']

            if (page[0:3] == '/m/' and GA_NEW.ix[count, 'exist'] != 0 and page not in stoppages):

                file_mobile = urllib.urlopen(url)
                content_mobile = file_mobile.read()
                file_mobile.close()
                url_mobile = re.findall(r'<li><a data-ajax="false" href="(.*?)">'\
                    'Desktop View</a></li>', content_mobile)

                if len(url_mobile) != 0: ##This statement check if there is valid mobile webpage
                    file_desktop = urllib.urlopen(url_mobile[0])
                    content_desktop = file_desktop.read()
                    file_desktop.close()
                    desktop_sign = re.findall(r'<meta property="og:'\
                            'url" content="(.*?)?overrideMobileRedirect=1', \
                            content_desktop)

                    if len(desktop_sign) != 0:
                        desktop_string = desktop_sign[0]
                        desktop_string = desktop_string.replace("amp;", "")
                        desktop = desktop_string[:-1]
                        GA_NEW.ix[count, 'url'] = desktop
                        url = desktop

                        if (GA_NEW.ix[count, 'exist'] == 1):
                            page_desktop = desktop[33:]
                        elif (GA_NEW.ix[count, 'exist'] == 2):
                            page_desktop = desktop[29:]
                        else:
                            page_desktop = desktop[26:]

                        ## Get index corresponding to desktop page and sum mobile+desktop pageviews
                        if len(list_page[list_page == page_desktop]) != 0:
                            index_desktop = list_page[list_page == page_desktop].index[0]
                            MOBILE_INDEX.append(count)
                            GA_NEW.ix[count, 'mobile'] = 1
                            ##Add data from mobile to Desktop
                            GA_NEW.ix[index_desktop, 'Pageviews'] = GA_NEW.ix[index_desktop, \
                            'Pageviews'] + GA_NEW.ix[count, 'Pageviews']
                            GA_NEW.ix[index_desktop, \
                            'Unique Pageviews'] = GA_NEW.ix[index_desktop, 'Unique Pageviews'] + \
                            GA_NEW.ix[count, 'Unique Pageviews']
                            GA_NEW.ix[index_desktop, 'Entrances'] = GA_NEW.ix[index_desktop, \
                            'Entrances'] + GA_NEW.ix[count, 'Entrances']

            if GA_NEW.ix[count, 'exist'] != 0:
                article = extract_title(url)
                GA_NEW.ix[count, 'Thereistitle'] = article[0]
                title = article[1]
                GA_NEW.ix[count, 'title'] = title
                GA_NEW.ix[count, 'Date'] = article[2]
                GA_NEW.ix[count, 'TimeSensitive'] = is_time_sensitive(title)
                count += 1
        page_num += 1
        print page_num, count

        #Waiting code
        if page_num%100 == 0:
            time.sleep(10)
        if page_num%1000 == 0:
            time.sleep(60)


    ##Delete rows corresponding to mobile becauase Desktop ones has been corrected
    mobile_drop = GA_NEW.drop(GA_NEW.index[MOBILE_INDEX])
    mobile_drop = GA_NEW[GA_NEW['mobile'] != 1]

    ##Delete rows corresponding to links either broken or do not exist
    link_drop = mobile_drop[mobile_drop['exist'] != 0]

    print 'data before time sensitive', len(link_drop)
    ##Delete rows corresponding to Timesensitive article ==''
    time_drop = link_drop[link_drop['TimeSensitive'] == 0]
    print 'data after time sensitive drop', len(time_drop)


    ##Delete rows corresponding to Date ==''
    date_drop = time_drop[time_drop['Date'] != '']

    date_drop['index'] = date_drop.index
    grouped = date_drop.groupby(['title'])
    indexdata = [gp_keys[0] for gp_keys in grouped.groups.values()]
    title_data = date_drop.reindex(indexdata)
    groupedindex = title_data.groupby(['index'])
    indexdata = [gp_keys[0] for gp_keys in groupedindex.groups.values()]
    unique_data = title_data.reindex(indexdata)
    unique_data.sort(['Pageviews'], ascending=False, inplace=True)
    unique_data.to_csv("MAR_FullTopBlogsDSCAB_1-10000.csv", sep=",", index=False, encoding='utf-8')

    ##Save data for Hootsuite
    data_to_save = unique_data[['title', 'url', 'Date', 'Pageviews']]
    file_output = "MAR_TopDSCABBlogsPage_1-10000" + FILE_NAME
    data_to_save.to_csv(file_output, sep=",", index=False, encoding='utf-8')


if __name__ == '__main__':
    main()
