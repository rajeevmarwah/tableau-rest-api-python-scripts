import requests
from configparser import ConfigParser
import xml.etree.ElementTree as ET
import os.path
import json


api_version = 3.4
xmlns = {'t': 'http://tableau.com/api'}

def main()
	#Location of the config  directory file to read credentials 
	inputpath=r'/install/credentials'
	propertiesfile=os.path.join(inputpath,'config.properties')
	configfile = ConfigParser()
	configfile.read(propertiesfile)
	#Reading the credentials, url and site name from config file
	username=configfile.get('tableau', 'username')
	password=configfile.get('tableau', 'password')
	server_url=configfile.get('tableau', 'server_url')
	site=configfile.get('tableau', 'site')
	#Calling the sign in function to sign in and get the token
	auth_token,site_id=sign_in(username,password,server_url,site)
	#Calling the query user on site to get groups on site
	queryusersonsite(server_url,auth_token,site_id)
	#Calling the query group on site function to get groups on site
	querygroupsonsite(server_url,auth_token,site_id)
	#Calling the function query workbook permissions on site  to get workbook permissions on site
	queryworkbookpermissions(server_url,auth_token,site_id)
	#Calling the function query datasource permissions on site  to get workbook permissions on site
	querydsperm(server_url,auth_token,site_id)
	#Calling the function query project permissions on site  to get workbook permissions on site
	queryprojectpermissions(server_url,auth_token,site_id)
	#Calling the function query view permissions on site  to get workbook permissions on site
	queryviewpermissions(server_url,auth_token,site_id)
#SIgn In function to get token
def sign_in(username,password,server_url,site):
	#Tableau Server URL 
	server_url_sign_in= server_url + "/api/{0}/auth/signin".format(api_version)
	#Forming the request body with the parent element tsRequest
	input_data=ET.Element('tsRequest')
	#Forming the request body for the child element
	input_credentials=ET.SubElement(input_data,'credentials', name=username,password=password)
	#Forming the next request for the child element along with credentials and parent element
	#this is all in XML format
	ET.SubElement(input_credentials,'site', contentUrl=site)
	input=ET.tostring(input_data)	
	#Body has been formed.Signing in
	input_signin=requests.post(server_url_sign_in, data=input,verify=False)
	#print(input_signin)
	server_response = input_signin.text.encode('ascii', errors="backslashreplace").decode('utf-8')
	get_output=ET.fromstring(server_response)
	#fromstring has 2 method find and get. find get the first child element and get the name.
	#Get the authentication token
	auth_token=get_output.find('t:credentials',xmlns).get('token')
	#Get the site id
	site_id=get_output.find('.//t:site', xmlns).get('id')
	#Return the auth token and site id
	return(auth_token, site_id)
#Query workbook permissions  block
def queryworkbookpermissions(server_url,auth_token,site_id):
	#Get the list of workbooks on the server to find permissions for each workbook
	url_queryworkbookonsite=server_url + "/api/{0}/sites/{1}/workbooks".format(api_version,site_id)
	#Getting the response in JSON format
	getworkbooksonsite=requests.get(url_queryworkbookonsite,headers={'Accept':'application/json','x-tableau-auth':auth_token})
	#Loading the data into python format
	json_data_wb=json.loads(getworkbooksonsite.text)
	#Create a dictionary for taking the value of permissions object
	tmp={}
	#Create an array to store all permissions key value
	final=[]
	#For loop to iterate through each workbook and get the permissions
	for item in json_data_wb['workbooks']['workbook']:
		#Retrive the luid for each workbook
		output=(item['id'])
		#Get permissions for each workbook
		url_getworkbookpermission= server_url + "/api/{0}/sites/{1}/workbooks/{2}/permissions".format(api_version,site_id,output)
		#Get the workbook permissions in json format
		getworkbookpermissions=requests.get(url_getworkbookpermission, headers={'Accept': 'application/json','x-tableau-auth':auth_token})
		getwbperm=getworkbookpermissions.json()
		#One rest API call is returning one json
		#Since we are executing multiple api calls , we are getting multiple json but Tableau understands only 1 json. We need to convert all rest api's call into a single json
		#Convert the incoming JSON string to an object using a JSON parser
		#Get the permissions block data from the call
		tmp=getwbperm["permissions"]
		#Apending all json  return data to one file
		final.append(tmp)
		#Dump the output in json format for Tableau to consume
		with open("data_output_learn.json", 'a+') as f:
			json.dump(final,f)
		#Close the file
	f.close()

#Query the users present on the site
def queryusersonsite(server_url,auth_token,site_id):
	getusers=server_url + "/api/{0}/sites/{1}/users".format(api_version,site_id)
	users=requests.get(getusers,headers={'x-tableau-auth':auth_token,'Accept':'application/json'})
	users_json=users.json()
	with open("users_data.json", 'w') as file:
		json.dump(users_json,file)
	file.close
#Function for query the groups present on the site	
def querygroupsonsite(server_url,auth_token,site_id):
	getgroups=server_url + "/api/{0}/sites/{1}/groups".format(api_version,site_id)
	groups=requests.get(getgroups,headers={'x-tableau-auth':auth_token,'Accept':'application/json'})	
	groups_json=groups.json()
	with open("groups_data.json", 'w') as file_gp:
		json.dump(groups_json,file_gp)
	file_gp.close
	
#Function for query the data sources permissions present on the site	
def querydsperm(server_url,auth_token,site_id):
	url_getds_list= server_url + "/api/{0}/sites/{1}/datasources".format(api_version,site_id)
	getds_list=requests.get(url_getds_list,headers={'x-tableau-auth':auth_token,'Accept':'application/json'})
	ds_json=getds_list.json()
	json_data_wb=json.loads(getds_list.text)
	#Creating Dictionary to hold key value pairs. It is holding all data
	ds_tmp={}
	#Creating an array to hold permissions
	ds_final=[]
	for item in json_data_wb['datasources']['datasource']:
		output=(item['id'])
		ds_perm= server_url + "/api/{0}/sites/{1}/datasources/{2}/permissions".format(api_version,site_id,output)
		get_ds_perm=requests.get(ds_perm,headers={'x-tableau-auth':auth_token,'Accept':'application/json'})
		json_ds_perm=get_ds_perm.json()
		ds_tmp=json_ds_perm["permissions"]
		ds_final.append(ds_tmp)
	with open("ds_data_json.json",'w') as file_ds:
		json.dump(ds_final,file_ds)
	file_ds.close

#Function for query the project permissions present on the site
def queryprojectpermissions(server_url,auth_token,site_id):
	url_getprjt_list= server_url + "/api/{0}/sites/{1}/projects".format(api_version,site_id)
	getprjt_list=requests.get(url_getprjt_list,headers={'x-tableau-auth':auth_token,'Accept':'application/json'})
	prjt_json=getprjt_list.json()
	json_data_wb=json.loads(getprjt_list.text)
	#Creating Dictionary to hold key value pairs. It is holding all data
	prjt_tmp={}
	#Creating an array to hold permissions
	prjt_final=[]
	for item in json_data_wb['projects']['project']:
		output=(item['id'])
		prjt_perm= server_url + "/api/{0}/sites/{1}/projects/{2}/permissions".format(api_version,site_id,output)
		get_prjt_perm=requests.get(prjt_perm,headers={'x-tableau-auth':auth_token,'Accept':'application/json'})
		json_prjt_perm=get_prjt_perm.json()
		prjt_tmp=json_prjt_perm["permissions"]
		prjt_final.append(prjt_tmp)
	with open("prjt_data_json.json",'w') as file_prjt:
		json.dump(prjt_final,file_prjt)
	file_prjt.close

#Function for query the view permissions present on the site
def queryviewpermissions(server_url,auth_token,site_id):
	url_getview_list= server_url + "/api/{0}/sites/{1}/views".format(api_version,site_id)
	getview_list=requests.get(url_getview_list,headers={'x-tableau-auth':auth_token,'Accept':'application/json'})
	view_json=getview_list.json()
	json_data_wb=json.loads(getview_list.text)
	#Creating Dictionary to hold key value pairs. It is holding all data
	view_tmp={}
	#Creating an array to hold permissions
	view_final=[]
	for item in json_data_wb['views']['view']:
		output=(item['id'])
		view_perm= server_url + "/api/{0}/sites/{1}/views/{2}/permissions".format(api_version,site_id,output)
		get_view_perm=requests.get(view_perm,headers={'x-tableau-auth':auth_token,'Accept':'application/json'})
		json_view_perm=get_view_perm.json()
		view_tmp=json_view_perm["permissions"]
		view_final.append(view_tmp)
	with open("view_data_json.json",'w') as file_view:
		json.dump(view_final,file_view)
	file_view.close

#In Main function
if __name__ == "__main__":
    main()
	