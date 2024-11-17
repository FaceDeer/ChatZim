import json
import requests

#Documentation: https://platform.openai.com/docs/api-reference/chat/create
#https://platform.openai.com/docs/api-reference/models

def queryLLM(messages, config):
    max_length = config.get("max_length", 1024)
    generateUrl = config.get("API_url", "http://10.0.0.149:5001/v1/chat/completions")
    api_key = config.get("API_key")
    org_id = config.get("org_id")
    project_id = config.get("project_id")
    model = config.get("model")
    headers = {'Content-Type': 'application/json'}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    if org_id:
        headers["OpenAI-Organization"] = org_id
    if project_id:
        headers["OpenAI-Project"] = project_id
    
    # Send the request and get the response
    try:
        data = {
            "messages": messages,
            "max_completion_tokens": max_length,
        }
        if model:
            data["model"] = model
        response = requests.post(generateUrl, headers=headers, data=json.dumps(data))
    except Exception as e:
          print(f"An error occurred: {e}")
          return False
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the response JSON into a Python dictionary
        response_data = json.loads(response.text)
        message = {"role": response_data["choices"][0]["message"]["role"],
                   "content": response_data["choices"][0]["message"]["content"]
                   }
        return message
    else:
        print(f"Request failed with status code {response.status_code}")
        return False

