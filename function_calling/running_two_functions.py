import requests                           # Importing requests package to connect to the weather URL
from dotenv import load_dotenv            # dotenv package is required to read the weather_api_key
from openai import OpenAI
import os                                 # To get the variable value of openai
from openai import OpenAI
import json                               # Needed to work json.dumps() and json.loads() to convert file from 'dict to str' and 'str to dict' datatypes respectively


# Section 1 - Set up the environment
load_dotenv()
client = OpenAI()
 
# Creating a variable to open-read-close the weather_function description file
f = open("function_calling/weather_function_description.txt","r")
WEATHER_DESCRIPTION = f.read()
f.close()

# Creating a variable to open-read-close the order_function description file
f = open("function_calling/order_data_function_description.txt","r")
ORDER_DESCRIPTION = f.read()
f.close()


# Define a weather function -1
def get_weather(zipcode):                  # zipcode parameter is mandatory for the function to run 
    country_code = "in"
    api_key = os.getenv("weather_api_key") # Gets a particular value from .env file, that is "weather_api_key" value
    url = f"https://api.openweathermap.org/data/2.5/weather?zip={zipcode},{country_code}&appid={api_key}" 
    result = requests.get(url)             # Making a request to the url
                                         
    response = result.json()               # This url will give the output as a json file
    return response

# weather_output = get_weather("520011")      # If needed testing if the created function is working or not
# print(weather_output)

# Line No. 34 and 35 are executed manually, but
# I want my AI to decide when my function is required and execute it at that time, for that we need openAI package

# For an AI to identify when to run and execute a function, it needs a function schema
# We have a function schema documentation in "https://developers.openai.com/api/docs/guides/function-calling" website

# Define a order function -2
def get_order_data(user_id):                  # zipcode parameter is mandatory for the function to run 
#    country_code = "in"
#    api_key = os.getenv("weather_api_key") # Gets a particular value from .env file, that is "weather_api_key" value
    url = f"https://localhost:8000/delivery/{user_id}"          # user_id is coming from line 39
    result = requests.get(url)             # Making a request to the url
                                         
    response = result.json()               # This url will give the output as a json file
    return response

# So, Now we are defining the function schema - Line 40-56 is fixed structure given by "OpenAI company"

openai_tools = [                                        # We can change the variable name to our choice
    {
        "type": "function",
        "name": "get_weather",                          # get_weather comes from Line 25
        "description": WEATHER_DESCRIPTION,             # WEATHER_DESCRIPTION comes from Line 15
        "parameters": {
            "type": "object",
            "properties": {
                "zipcode": {                            # zipcode is the parameter of our function, refer line 19
                    "type": "string",                   # string is the data type of the parameter, zipcode
                    "description": "This is the zipcode of the location, we need the weather data of",
                },
            },
            "required": ["zipcode"],                    # required is the mandatory values for the function to run
        }
    },
        ### This the function schema for 2nd function ----> get_order_data(user_id)

    {
        "type": "function",
        "name": "get_order_data",                      # get_order_data comes from Line 45
        "description": ORDER_DESCRIPTION,              # ORDER_DESCRIPTION comes from Line 20
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {                           # user_id is the parameter of our function, refer line 19
                    "type": "integer",                 # striintegerng is the data type of the parameter, user_id
                    "description": "This is the userid of the customer, we need to fetch the order status of",
                },
            },
            "required": ["user_id"],                   # required is the mandatory values for the function to run
        }
    }
]


# This is the function schema written for two function to execute, 
# we have multiple functions to run, we are writing a new function schema for every function

# Next, we ask for a user_question

user_question = input("HUMAN INPUT: Please ask me a question, happy to answer: ")

# Making an LLM call
response = client.responses.create(
    model="gpt-5.4-mini",
#   reasoning={"effort":"high"},
#   input="Steps to make a cup of coffee?",
    input=user_question,
#   instructions=SYSTEM_PROMPT
    tools = openai_tools                # Define our function schema, which is openai_tools, refer line no. 40
)

# Right now, AI is not running the tool. Because AI does not have ability to run the tool automatically
# print(response.output)

# Refer to "running_single_function.py" how output looks like a list
# Here output in both cases from line 79 - 111. Both of them are list,
# Step-1: We create an empty list[]
# Step-2: We execute the function as per the requirement
# Step-3: Take the output of the function and store in the empty list created in Step-1
# Step-4: Now, give this list with data, to AI, to summarize into human readable manner
# To execute above steps,

function_output = []                # Created an empty list

for item in response.output:
#   print(item.type)                # Output is "message" for regular questions and "function call" for weather related because it runs the function
    if item.type == "function_call":
#       print(item.arguments)       # Output is {"zipcode":"380001"}, if question is Weather in Ahmedabad
        args = json.loads(item.arguments)
#       print(args)                 # Output is {'zipcode':'380001'}, if question is Weather in Ahmedabad
        if item.name =="get_weather":
            results = get_weather(args['zipcode'])
            print("THIS IS A RAW FUNCTION OUTPUT")
            print("------------------------------")
            print(results)  
            
        elif item.name =="get_order_data":                      # This code fragment executes if question is related to orders_status
            results = get_order_data(args['user_id'])
            print("THIS IS A RAW FUNCTION OUTPUT")
            print("------------------------------")
            print(results)
            
        else:
            results = "unknown function called"        # Output is 380001, if question is Weather in Ahmedabad

# Now assign the RAW OUTPUT to the created list on line no. 121
        function_output.append({
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps({"result":results})   # json.dumps() to convert dict to str
        })

# Now make a 2nd LLM call / api call to summarize this list with data loaded
final_response = client.responses.create(
    model="gpt-5.4-mini",
#   reasoning={"effort":"high"},
#   input="Steps to make a cup of coffee?",
    input=function_output,                 # function_output is coming from line no.141
    previous_response_id=response.id       # response is coming from line no. 68, our 1st LLM call response, --> This is fetching the previous conversation
  )

print("AI SUMMARIZED OUTPUT")
print("---------------------")
print(final_response.output_text)
