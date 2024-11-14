import json
import requests

#Documentation: https://platform.openai.com/docs/api-reference/chat/create
#https://platform.openai.com/docs/api-reference/models


# Define the URL
generateUrl = "http://10.0.0.149:5001/v1/chat/completions"

# Define the headers for the request
headers = {
    'Content-Type': 'application/json',
    #"Authorization: Bearer $OPENAI_API_KEY",
}


def queryLLM(messages, max_length = 1024):
    # Send the request and get the response
    try:
        data = {
            #"model": ,
            "messages": messages,
            "max_completion_tokens": max_length,
        }
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

def test():
    result = queryLLM([
      {
        "role": "system",
        "content": "You are a helpful assistant."
      },
      {
        "role": "user",
        "content": "Hello!"
      }
    ])

    print(result)

#test()
