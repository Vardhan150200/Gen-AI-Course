import requests                           # Importing requests package to connect to the weather URL
from dotenv import load_dotenv            # dotenv package is required to read the weather_api_key
from openai import OpenAI
import os                                 # To get the variable value of openai
from openai import OpenAI
import json                            

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
    api_key = os.getenv("weather_api_key") 
    url = f"https://api.openweathermap.org/data/2.5/weather?zip={zipcode},{country_code}&appid={api_key}" 
    result = requests.get(url)             # Making a request to the url
                                         
    response = result.json()               # This url will give the output as a json file
    return response
 
# Define a order function -2
def get_order_data(user_id):                  # zipcode parameter is mandatory for the function to run 
    url = f"https://localhost:8000/delivery/{user_id}"         
    result = requests.get(url)             # Making a request to the url
                                         
    response = result.json()               # This url will give the output as a json file
    return response

openai_tools = [                                       
    {
        "type": "function",
        "name": "get_weather",                       
        "description": WEATHER_DESCRIPTION,            
        "parameters": {
            "type": "object",
            "properties": {
                "zipcode": {                            
                    "type": "string",                   # string is the data type of the parameter, zipcode
                    "description": "This is the zipcode of the location, we need the weather data of",
                },
            },
            "required": ["zipcode"],                    # required is the mandatory values for the function to run
        }
    },
        ### This the function schema for 2nd function -
    {
        "type": "function",
        "name": "get_order_data",                
        "description": ORDER_DESCRIPTION,              
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {                           
                    "type": "integer",                
                    "description": "This is the userid of the customer, we need to fetch the order status of",
                },
            },
            "required": ["user_id"],                   # required is the mandatory values for the function to run
        }
    }
]

user_question = input("HUMAN INPUT: Please ask me a question, happy to answer: ")

# Making an LLM call
response = client.responses.create(
    model="gpt-5.4-mini",
    input=user_question,
    tools = openai_tools                
)

function_output = []                # Created an empty list

for item in response.output:
    if item.type == "function_call":
        args = json.loads(item.arguments)
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
            results = "unknown function called"       

        function_output.append({
            "type": "function_call_output",
            "call_id": item.call_id,
            "output": json.dumps({"result":results})   # json.dumps() to convert dict to str
        })

# Now make a 2nd LLM call / api call to summarize this list with data loaded
final_response = client.responses.create(
    model="gpt-5.4-mini",
    input=function_output,                
    previous_response_id=response.id      
  )

print("AI SUMMARIZED OUTPUT")
print("---------------------")
print(final_response.output_text)
