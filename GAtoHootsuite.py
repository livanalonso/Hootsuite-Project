#!/usr/bin/python2.7 -tt

##Import libraries
import pandas as pd
from numpy  import *
import httplib
from urlparse import urlparse
import re
import urllib
import html2text
import requests
import time
import os.path

##Read Google Analytics file to be analyzed
file=raw_input("Enter Google Analytics file name: ")
ga_new=pd.read_csv(file,skiprows=6,nrows=10000,thousands=',')

##Read previous output file
output=raw_input("Enter previous output file: ")
if os.path.isfile(output):
        old_data=pd.read_csv(output)
old_page=old_data['Page'].astype(str).values

##Read previous input file (help to do not process twice old data)
file_old='Analytics DataScienceCentral.com Pages 20110901-20150228_10000.csv'
ga_old=pd.read_csv(file_old,skiprows=6,nrows=6400,thousands=',')

##print ga_old['Page']

## Initializing new columns and variables
ga_new['mobile']=0
ga_new['TimeSensitive']=0
ga_new['ThereisTitle']=0
ga_new['Title']=''
ga_new['Date']=''
ga_new['exist']=0
ga_new['url']=""

mobile_index=[]

## This function return if page belongs to either DSC, AB , BDN or it does not exist.
## Create new column with values 1,2,3 or 0 respectively
def url_check(page):
	dsc='http://www.datasciencecentral.com'
	ab='http://www.analyticbridge.com'
	bdn='http://www.bigdatanews.com'
	url=dsc+page
	resp = requests.get(url)
	if (resp.status_code < 400):
		number=1
		checkurl=url
	else:
		url=ab+page
		resp = requests.get(url)	
		if (resp.status_code < 400):
			number=2
			checkurl=url
		else:
			url=bdn+page
			resp = requests.get(url)
			if (resp.status_code < 400):
				number=3
				checkurl=url
			else:
				number=0
				checkurl=""
	return [number,checkurl]

## Function for extracting title and published date of Blog
def extract_title(url):
	titlefile=urllib.urlopen(url)
	sourceCode=titlefile.read()
	titlefile.close()
	splitTitle=re.findall(r'<meta property="og:title" content="(.*?)" />',sourceCode)
	splitDate=re.findall('</a><a class="nolink"> on (.*?)at',sourceCode)
	
	if len (splitTitle)!=0:
		thereisTitle=1
		Title=html2text.html2text(''.join(splitTitle))
		Title=Title.replace('\n','')
	else:
		thereisTitle=0
		Title=''
	
	if len (splitDate)!=0:
		date=''.join(splitDate)
	else:
		date=''	
	return [thereisTitle,Title,date]

## Function evaluate if article could be time sensitive according list of words
def isTimeSensitive(title):
	count=0
	number=0
	timestop=['weekly digest','webinar','conference','summit','upcoming']
	years=['2010','2011','2012','2013']
	months=['january', 'february','march','april','may','june','july','august','september','october','november','december']
	timestop=timestop+months+years
	while number==0 and count<len(timestop):
		if re.search(timestop[count],title.lower())!=None:
			number=1
		count+=1
	return number

def populate_page(page,old):
        if page in old:
                return [True,where(old==page)[0]]
        else:
                return [False,'']
        
## Main function
def main ():
        page_num=0
        count=0
        list_page=ga_new['Page']

        for page in list_page:

                #Update old data with new data
                if populate_page(page,old_page)[0]:
                        ##print 'inside copying old data'
                        ## Get index corresponding to old data
                        page_index=populate_page(page,old_page)[1][0]
                        columns_tocopy=['mobile','exist','TimeSensitive','ThereisTitle','Title','Date','exist','url']
                        ga_new.ix[count,columns_tocopy]=old_data.ix[page_index,columns_tocopy]
                        columns_toreplace=['Pageviews','Unique Pageviews','Avg. Time on Page','Entrances','Bounce Rate','% Exit','Page Value']
                        ga_new.ix[count,columns_toreplace]=old_data.ix[page_index,columns_toreplace]
                        count+=1

                #Check if the web was analized and did not pass selection criteria, then do nothing
                elif page in ga_old['Page'].values:
                        a=1
                        ##print 'did not pass selection criteria'                      

                ## Populate new data
                else:
                        ##print 'inside new data'
                        ## Call function url_check(page) to check if page belongs to either DSC, AB , BDN or it does not exist. Create new column with values 1,2,3 or 0 respectively
                        ga_new.ix[count,'exist']=url_check(page)[0]
                        url=url_check(page)[1]
                        ga_new.ix[count,'url']=url
                
                        ##The following code analyzes if the page is mobile page and correct number of Pageviews, Unique Pageviews and Entrances from Desktop link
                        stoppages=['/jobs/search','/m/404','/m/signup','/m/signin?target=http://www.datasciencecentral.com/profiles/profile/emailSettings?xg_source=msg_mes_network','/m/signup?target=/m&cancelUrl=/m','/m/signin?target=/m&cancelUrl=/m','/jobs/search/results?page=2','/forum?page=4','/jobs/search/advanced','/profiles/blog/list?page=3','/profiles/settings/editPassword','/main/invitation/new?xg_source=userbox','/main/authorization/passwordResetSent?previousUrl=http://www.analyticbridge.com/main/authorization/doSignIn?target=http://www.analyticbridge.com/','/profiles/friend/list?page=4','/main/index/banned','/main/invitation/new?xg_source=empty_list']
                
                        if (page[0:3]=='/m/' and ga_new.ix[count,'exist']!=0 and page not in stoppages):

                                file_mobile=urllib.urlopen(url)
                                content_mobile=file_mobile.read()
                                file_mobile.close()
                                url_mobile=re.findall(r'<li><a data-ajax="false" href="(.*?)">Desktop View</a></li>',content_mobile)
                        
                                if len(url_mobile)!=0: ##This statement check if there is valid mobile webpage
                                        file_desktop=urllib.urlopen(url_mobile[0])
                                        content_desktop=file_desktop.read()
                                        file_desktop.close()
                                        desktop_sign=re.findall(r'<meta property="og:url" content="(.*?)?overrideMobileRedirect=1',content_desktop)
                                
                                        if len(desktop_sign)!=0:
                                                desktop_string=desktop_sign[0]
                                                desktop_string=desktop_string.replace("amp;","")
                                                desktop=desktop_string[:-1]
                                                ga_new.ix[count,'url']=desktop
                                                url=desktop
                                
                                                if (ga_new.ix[count,'exist']==1):
                                                        page_desktop=desktop[33:]
                                                elif (ga_new.ix[count,'exist']==2):
                                                        page_desktop=desktop[29:]
                                                else:
                                                        page_desktop=desktop[26:]
                        
                                                ## Get index corresponding to desktop page and sum mobile+desktop pageviews
                                                if len(list_page[list_page==page_desktop])!=0: 
                                                        index_desktop=list_page[list_page==page_desktop].index[0]
                                                        mobile_index.append(count)
                                                        ga_new.ix[count,'mobile']=1
                        
                                                        ##Add data from mobile to Desktop
                                                        ga_new.ix[index_desktop,'Pageviews']=ga_new.ix[index_desktop,'Pageviews']+ga_new.ix[count,'Pageviews']	
                                                        ga_new.ix[index_desktop,'Unique Pageviews']=ga_new.ix[index_desktop,'Unique Pageviews']+ga_new.ix[count,'Unique Pageviews']
                                                        ga_new.ix[index_desktop,'Entrances']=ga_new.ix[index_desktop,'Entrances']+ga_new.ix[count,'Entrances']

                        if ga_new.ix[count,'exist']!=0:
                                article=extract_title(url)
                                ga_new.ix[count,'ThereisTitle']=article[0]
                                title=article[1]
                                ga_new.ix[count,'Title']=title
                                ga_new.ix[count,'Date']=article[2]
                                ga_new.ix[count,'TimeSensitive']=isTimeSensitive(title)
                
                        #print count, ga_new.ix[count,'Title'],ga_new.ix[count,'url'],'---',ga_new.ix[count,'TimeSensitive'],'---'#,ga_new.ix[count,'Date']
                        count+=1
                page_num+=1
                print page_num,count
	
		#Waiting code
                if page_num%100==0:
                        time.sleep(10)
                if page_num%1000==0:
                        time.sleep(60)


	##Delete rows corresponding to mobile becauase Desktop ones has been corrected

        mobileDrop=ga_new.drop(ga_new.index[mobile_index])
        mobileDrop=ga_new[ga_new['mobile']!=1]

	##Delete rows corresponding to links either broken or do not exist
        linkDrop=mobileDrop[mobileDrop['exist']!=0]	

        print 'data before time sensitive',len(linkDrop)
	##Delete rows corresponding to Timesensitive article ==''
        timeDrop=linkDrop[linkDrop['TimeSensitive']==0]	
        print 'data after time sensitive drop',len(timeDrop)


	##Delete rows corresponding to Date ==''
        dateDrop=timeDrop[timeDrop['Date']!='']	

        dateDrop['index']=dateDrop.index
        grouped = dateDrop.groupby(['Title'])
        indexdata = [gp_keys[0] for gp_keys in grouped.groups.values()]
        Title_data = dateDrop.reindex(indexdata)
        groupedindex = Title_data.groupby(['index'])
        indexdata = [gp_keys[0] for gp_keys in groupedindex.groups.values()]
        unique_data = Title_data.reindex(indexdata)
        unique_data.sort(['Pageviews'], ascending=False,inplace=True)
        unique_data.to_csv("FullTopBlogsDSCAB_1-10000.csv",sep=",", index = False, encoding='utf-8')

	##Save data for Hootsuite
        data_to_save=unique_data[['Title','url','Date','Pageviews']]
        fileName="TopDSCABBlogsPage_1-10000"+file
        data_to_save.to_csv(fileName,sep=",", index = False, encoding='utf-8')


	
if __name__=='__main__':
	main()
