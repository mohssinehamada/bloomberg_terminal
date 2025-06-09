import json
from pathlib import Path
from collections import defaultdict

# Define input and output file paths
input_file = Path("./output/agent_actions.json")
output_file = Path("./output/grouped_agent_actions.json")

# Load the original JSON data
if input_file.exists():
    with open(input_file, "r") as f:
        try:
            actions = json.load(f)
        except json.JSONDecodeError:
            actions = []
else:
    actions = []

# Group actions by task
grouped_data = defaultdict(list)
for action in actions:
    task_number = action["task"]
    grouped_data[task_number].append(action)

# Convert to the required format
final_output = [{"task": task, "results": results} for task, results in grouped_data.items()]

# Save the grouped data to a new JSON file
with open(output_file, "w") as f:
    json.dump(final_output, f, indent=4)

print(f"Grouped JSON file saved at: {output_file}")
