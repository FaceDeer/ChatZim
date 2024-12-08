import json
import requests

#Documentation: https://platform.openai.com/docs/api-reference/chat/create
#https://platform.openai.com/docs/api-reference/models

def queryLLM(messages, config):
    max_length = config.get("max_length", 1024)
    generateUrl = config.get("api_url", "http://localhost:5001/v1/chat/completions")
    api_key = config.get("api_key")
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
            "stream": False,
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

def queryLLMStreamed(messages, config):
    max_length = config.get("max_length", 1024)
    generateUrl = config.get("api_url", "http://localhost:5001/v1/chat/completions")
    api_key = config.get("api_key")
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
    data = {
        "messages": messages,
        "max_completion_tokens": max_length,
        "stream": True  # Enable streaming
    }

    try:
        with requests.post(generateUrl, headers=headers, data=json.dumps(data), stream=True) as response:
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line and line != b'data: [DONE]':
                        try:
                            yield json.loads(line.decode('utf-8')[len("data: "):])
                        except Exception as e:
                            print(f"An error in json decoding occurred: {e}")
                            print("Line was:")
                            print(line)
                            yield None
            else:
                print(f"Request failed with status code {response.status_code}")
                yield None
    except Exception as e:
        print(f"An error occurred: {e}")
        yield None

