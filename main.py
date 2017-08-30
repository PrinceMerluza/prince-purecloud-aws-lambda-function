import base64
import json
from datetime import datetime, timedelta

import PureCloudPlatformClientV2
from PureCloudPlatformClientV2.rest import ApiException
import requests
from pprint import pprint


def main_handler(event, context):
	#oauth 2
	clientId = 'ad50ef2f-c4be-4f8a-8fee-996fafadaa61'
	clientSecret = 'zm_BbfM8XqCKPizLAty1W4qZzw9vYQkDNFbyAzGFKWw'
	authorization = base64.b64encode(bytes(clientId + ':' + clientSecret, 'ISO-8859-1')).decode('ascii')

	requestHeaders = {
		'Authorization': 'Basic ' + authorization,
		'Content-Type': 'application/x-www-form-urlencoded'
	}
	requestBody = {
		'grant_type': 'client_credentials'
	}	

	response = requests.post('https://login.mypurecloud.com/oauth/token', data=requestBody, headers=requestHeaders)
		
	#Put token for SDK
	PureCloudPlatformClientV2.configuration.access_token = response.json()['access_token']

	#API Calls
	conversationsApi = PureCloudPlatformClientV2.ConversationsApi()
	usersApi = PureCloudPlatformClientV2.UsersApi()

	participantDetailsDict = {} # dict for participant id -> {user id, username, email ad}

	#get call history of all in org
	try:
		body = PureCloudPlatformClientV2.ConversationQuery()
		now = datetime.utcnow()
		yesterday = now - timedelta(days = 1)
		
		body.interval = str(yesterday.year) + "-" + padZero(yesterday.month) + "-" + padZero(yesterday.day) + "T" + padZero(yesterday.hour) + ":" + padZero(yesterday.minute) + ":00.000Z/" + \
						str(now.year) + "-" + padZero(now.month) + "-" + padZero(now.day) + "T" + padZero(now.hour) + ":" + padZero(now.minute) + ":00.000Z"
		print(body.interval)
		#"2017-08-23T16:00:00.000Z/2017-08-24T16:00:00.000Z"
		body.order = 'desc'
		body.order_by = "conversationStart"
		body.paging = PureCloudPlatformClientV2.PagingSpec()
		body.paging.page_size = 25
		body.paging.page_number = 1
		
		api_response = conversationsApi.post_analytics_conversations_details_query(body)
		#pprint(api_response)
		for convo in api_response.conversations:
			for participant in convo.participants:
				if participant.purpose == "user" or participant.purpose == "agent":
					print(participant.participant_id)
					participantDetailsDict[participant.participant_id] = {'user_id': participant.user_id}
	except ApiException as e:
		return "Error %s\n" % e
		
		
	#get details of the user
	try:
		for k, v in participantDetailsDict.items():
			api_response = usersApi.get_user(v['user_id'])
			v['user_name'] = api_response.username
			v['email'] = api_response.email
			
	except ApiException as e:
		return "Error %s\n" % e

	# set up return for this service
	queriedValues = participantDetailsDict.get(event['participant_id'],'none')
	if queriedValues == 'none':
		return "ERROR"
	else:
		return 'User ID: ' + queriedValues['user_id'] + '\nUser Name: ' + queriedValues['user_name'] + '\nEmail: ' + queriedValues['email']
	
	#for k, v in participantDetailsDict.items():
	#	print(k + ' : ' + v['user_id'] + ' : ' + v['user_name'] + ' : ' + v['email'])
	
def padZero(number):
	if(number < 10):
		return "0" + str(number)
	else:
		return str(number)