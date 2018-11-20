import json 
import requests 
import pandas as pd

# Author: Evan Gillespie (LeanIX)
#
# Adapted from:
# https://github.com/leanix-public/scripts/blob/master/cleanupOrphanedRelations/cleanupOrphanedRelations.py
#


# Create an API token in Pathfinder via Administration -> API Tokens
# auth_url and request_url is set to one of three urls:
#
# app.leanix.net for non-US users without a custom hostname
#
# auth_url = 'https://app.leanix.net/services/mtm/v1/oauth2/token' 
# request_url = 'https://app.leanix.net/services/pathfinder/v1/graphql' 
#
# app.leanix.net for US users without a custom hostname
#
# auth_url = 'https://us.leanix.net/services/mtm/v1/oauth2/token' 
# request_url = 'https://us.leanix.net/services/pathfinder/v1/graphql'
#  
# <HOSTNAME>.leanix.net for all workspaces with a custom hostname
#
# auth_url = 'https://<HOSTNAME>.leanix.net/services/mtm/v1/oauth2/token' 
# request_url = 'https://<HOSTNAME>.leanix.net/services/pathfinder/v1/graphql' 

api_token = 'API TOKEN AS STRING HERE'
auth_url = 'https://app.leanix.net/services/mtm/v1/oauth2/token' 
request_url = 'https://app.leanix.net/services/pathfinder/v1/graphql' 

# Get the bearer token - see https://dev.leanix.net/v4.0/docs/authentication
response = requests.post(auth_url, auth=('apitoken', api_token),
                         data={'grant_type': 'client_credentials'})
response.raise_for_status() 
access_token = response.json()['access_token']
auth_header = 'Bearer ' + access_token
header = {'Authorization': auth_header}

# General function to call GraphQL given a query
def call(query):
  data = {"query" : query}
  json_data = json.dumps(data)
  response = requests.post(url=request_url, headers=header, data=json_data)
  response.raise_for_status()
  return response.json()

def externalIdtoApplicationId():
  query = """
    {
  allFactSheets(filter: {facetFilters: [{facetKey: "FactSheetTypes", keys: ["Application"]}, {facetKey: "TrashBin", keys: ["archived"]}]}) {
    totalCount
    edges {
      node {
        ... on Application {
          id
          name
          rev
          status
          externalId{
            externalId
          }
          applicationId
        }
      }
    }
  }
}
    """
  response = call(query)
  
  for appNode in response['data']['allFactSheets']['edges']:
    appId = appNode['node']['id']
    externalId = appNode['node']['externalId']
    print(appNode)
  #  relations = appNode['node']['relApplicationToProcess']['edges']
  #  externalIds = appNode['node']['externalId']
    
    if(externalId != None):
        print(externalId["externalId"])
        value = externalId["externalId"]
        patches = ["{op: replace, path: \"/status\", value: \"ACTIVE\"}"]
        patches.append("{op: replace, path: \"/applicationId\", value: \"" + value + "\"}")
        update(appId, "Undelete for cleanup", ",".join(patches))
        update(appId, "Redelete", "{op: replace, path: \"/status\", value: \"ARCHIVED\"}")
    
def update(app, comment, patches) :
  query = """
    mutation {
      updateFactSheet(id: "%s", comment: "%s", patches: [%s], validateOnly: false) {
        factSheet {
          id
        }
      }
    }
  """ % (app, comment, patches)
  print(comment + ":" + app)
  response = call(query)
  print(response)

# Start of the main program
externalIdtoApplicationId()
