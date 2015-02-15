#Import libraries
import pandas as pd
from numpy  import *
import httplib
from urlparse import urlparse
import re
import urllib
import html2text
import requests

#Read Google Analytics file
file=raw_input("Enter Google Analytics file name: ")
data=pd.read_csv(file,skiprows=6,nrows=5000)

##Convert comma separated values to values without comma
data['Pageviews']=[x.replace(",","") for x in data['Pageviews']]
data['Unique Pageviews']=[x.replace(",","") for x in data['Unique Pageviews']]
data['Entrances']=[x.replace(",","") for x in data['Entrances']]

##Covert strings to float	
data[['Pageviews','Unique Pageviews','Entrances']]=data[['Pageviews','Unique Pageviews','Entrances']].astype(float)
data['mobile']=0
count=0
mobile_index=[]
list_page=data['Page']
count=0;

for page in list_page:
	##Check if page belongs to either DSC, AB or it does not exist. Create new column with values 1,2,0 respectively
	dsc='http://www.datasciencecentral.com'
	ab='http://www.analyticbridge.com'
	bdn='http://www.bigdatanews.com'
	
	url=dsc+page
	resp = requests.get(url)
	
	if (resp.status_code < 400):
		data.ix[count,'exist']=1
		data.ix[count,'url']=url
	else:
		url=ab+page
		resp = requests.get(url)
	
		if (resp.status_code < 400):
			data.ix[count,'exist']=2
			data.ix[count,'url']=url
		else:
			url=bdn+page
			resp = requests.get(url)
	
			if (resp.status_code < 400):
				data.ix[count,'exist']=3
				data.ix[count,'url']=url
			else:
				data.ix[count,'exist']=0
				data.ix[count,'url']=""
	
	##The following code analyzes if the page is mobile page and correct number of Pageviews, Unique Pageviews and Entrances from Desktop link
	stoppages=['/m/404','/m/signup','/m/signin?target=http://www.datasciencecentral.com/profiles/profile/emailSettings?xg_source=msg_mes_network','/m/signup?target=/m&cancelUrl=/m','/m/signin?target=/m&cancelUrl=/m','/jobs/search/results?page=2','/forum?page=4','/jobs/search/advanced','/profiles/blog/list?page=3','/profiles/settings/editPassword','/main/invitation/new?xg_source=userbox','/main/authorization/passwordResetSent?previousUrl=http://www.analyticbridge.com/main/authorization/doSignIn?target=http://www.analyticbridge.com/','/profiles/friend/list?page=4','/main/index/banned','/main/invitation/new?xg_source=empty_list']
	
	if (page[0:3]=='/m/' and data.ix[count,'exist']!=0 and page not in stoppages):
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
				data.ix[count,'url']=desktop
				url=desktop
			
				if (data.ix[count,'exist']==1):
					page_desktop=desktop[33:]
				elif (data.ix[count,'exist']==2):
					page_desktop=desktop[29:]
				else:
					page_desktop=desktop[26:]
		
				## Get index corresponding to desktop page and sum mobile+desktop pageviews
				if len(list_page[list_page==page_desktop])!=0: 
					index_desktop=list_page[list_page==page_desktop].index[0]
					mobile_index.append(count)
					data.ix[count,'mobile']=1
		
					##Add data from mobile to Desktop
					data.ix[index_desktop,'Pageviews']=data.ix[index_desktop,'Pageviews']+data.ix[count,'Pageviews']	
					data.ix[index_desktop,'Unique Pageviews']=data.ix[index_desktop,'Unique Pageviews']+data.ix[count,'Unique Pageviews']
					data.ix[index_desktop,'Entrances']=data.ix[index_desktop,'Entrances']+data.ix[count,'Entrances']

	## Extract title of Blog
	titlefile=urllib.urlopen(url)
	sourceCode=titlefile.read()
	titlefile.close()
	splitTitle=re.findall(r'<meta property="og:title" content="(.*?)" />',sourceCode)
	splitDate=re.findall('</a><a class="nolink"> on (.*?)at',sourceCode)


	if len (splitTitle)!=0:
		data.ix[count,'ThereisTitle']=1
		data.ix[count,'Title']=html2text.html2text(''.join(splitTitle))
		data.ix[count,'Title']=data.ix[count,'Title'].replace('\n','')
	else:
		data.ix[count,'ThereisTitle']=0
		data.ix[count,'Title']=''

	if len (splitDate)!=0:
		##DatePub=time.strptime(''.join(splitDate),'%B %d, %Y')
		data.ix[count,'Date']=''.join(splitDate)

	else:
		data.ix[count,'Date']=''	
	
	print count, data.ix[count,'Title'],url,data.ix[count,'Date']
	
	count=count+1
	
	##Waiting code
	if count%10==0:
		time.sleep(10) 
	if count%200==0:
		time.sleep(60) 

##Delete rows corresponding to mobile becauase Desktop ones has been corrected
mobileDrop=data.drop(data.index[mobile_index])
mobileDrop=data[data['mobile']!=1]

##Delete rows corresponding to links either broken or do not exist
linkDrop=mobileDrop[mobileDrop['exist']!=0]	

##Delete rows corresponding to Date ==''
dateDrop=linkDrop[linkDrop['Date']!='']	

dateDrop['index']=dateDrop.index
grouped = dateDrop.groupby(['Title'])
indexdata = [gp_keys[0] for gp_keys in grouped.groups.values()]
Title_data = dateDrop.reindex(indexdata)
groupedindex = Title_data.groupby(['index'])
indexdata = [gp_keys[0] for gp_keys in groupedindex.groups.values()]
unique_data = Title_data.reindex(indexdata)
unique_data.to_csv("FullTopBlogsDSCAB5000.csv",sep=",", index = False, encoding='utf-8')

##Save data for Hootsuite
data_to_save=unique_data[['Title','url','Date','Pageviews']]
fileName="TopDSCABBlogsPage"+file
data_to_save.to_csv(fileName,sep=",", index = False, encoding='utf-8')




