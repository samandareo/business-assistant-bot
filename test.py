import json

# Step 1: Specify the file path where your JSON file is located
file_path = 'polls/poll_data.json'

# Step 2: Read the existing data from the JSON file
try:
    with open(file_path, 'r') as json_file:
        data = json.load(json_file)  # Load existing data into a Python dictionary
except FileNotFoundError:
    data = {}  # If file doesn't exist, start with an empty dictionary

# Step 3: Define new data that you want to add
new_poll = {
    "poll_id_3": {
        "question": "What's your favorite fruit?",
        "options": ["Apple", "Banana", "Orange", "Mango"],
        "votes": {}
    }
}

# Step 4: Update the existing data with the new data
data.update(new_poll)

# Step 5: Write the updated data back to the JSON file
with open(file_path, 'w') as json_file:
    json.dump(data, json_file, indent=4)  # 'indent=4' is optional for pretty formatting
    print(f"New data has been added to '{file_path}'.")
