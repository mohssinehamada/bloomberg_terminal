import json
from pathlib import Path

# Define file paths
grouped_file = Path("./output/grouped_agent_actions.json")
benchmark_file = Path("./data/benchmarktasksshort.json")
output_file = Path("./output/final_results.json")

# Load the grouped agent actions
if grouped_file.exists():
    with open(grouped_file, "r") as f:
        try:
            grouped_actions = json.load(f)
        except json.JSONDecodeError:
            grouped_actions = []
else:
    grouped_actions = []

# Load the benchmark tasks
if benchmark_file.exists():
    with open(benchmark_file, "r") as f:
        try:
            benchmark_tasks = json.load(f)
        except json.JSONDecodeError:
            benchmark_tasks = []
else:
    benchmark_tasks = []

# Create a dictionary mapping task numbers to grouped actions
task_to_actions = {entry["task"]: entry["results"] for entry in grouped_actions}

# Generate the final results
final_results = []

for task_number, benchmark in enumerate(benchmark_tasks, start=1):
    # Retrieve the first k agent actions for the given task
    agent_actions = task_to_actions.get(task_number, [])
    chosen_action = {
        str(i + 1): agent_actions[i]["tool_name"].lower()
        for i in range(len(benchmark["action"])) if i < len(agent_actions)
    }
    
    # Retrieve the desired k actions
    desired_action = {str(k): v.lower() for k, v in benchmark["action"].items()}
    
    # Compare actions
    action_matched = {
        k: chosen_action.get(k, "") == v for k, v in desired_action.items()
    }

    final_results.append({
        "task": task_number,
        "results": {
            "objective": benchmark.get("objective", ""),
            "url": benchmark.get("url", ""),
            "chosen_action": chosen_action,
            "desired_action": desired_action,
            "action_matched": action_matched
        }
    })

# Save the final results to a new JSON file
with open(output_file, "w") as f:
    json.dump(final_results, f, indent=4)

# Calculate and print metrics
total_actions = 0
matching_actions = 0
total_click_actions = 0
total_predicted_click_actions = 0
matching_click_actions = 0
total_type_actions = 0
total_predicted_type_actions = 0
matching_type_actions = 0
total_scroll_actions = 0
total_predicted_scroll_actions = 0
matching_scroll_actions = 0
total_return_value_actions = 0
total_predicted_return_value_actions = 0
matching_return_value_actions = 0

for entry in final_results:
    action_matched = entry["results"]["action_matched"]
    desired_action = entry["results"]["desired_action"]
    predicted_action = entry["results"]["chosen_action"]

    total_actions += len(action_matched)
    matching_actions += sum(action_matched.values())

    for k, action in desired_action.items():
        if action == "click":
            total_click_actions += 1
            if action_matched.get(k, False):
                matching_click_actions += 1
    for k, action in predicted_action.items():
        if action == "click":
            total_predicted_click_actions += 1

    for k, action in desired_action.items():
        if action == "type":
            total_type_actions += 1
            if action_matched.get(k, False):
                matching_type_actions += 1
    for k, action in predicted_action.items():
        if action == "type":
            total_predicted_type_actions += 1

    for k, action in desired_action.items():
        if action == "scroll":
            total_scroll_actions += 1
            if action_matched.get(k, False):
                matching_scroll_actions += 1
    for k, action in predicted_action.items():
        if action == "scroll":
            total_predicted_scroll_actions += 1

    for k, action in desired_action.items():
        if action == "return_value":
            total_return_value_actions += 1
            if action_matched.get(k, False):
                matching_return_value_actions += 1
    for k, action in predicted_action.items():
        if action == "return_value":
            total_predicted_return_value_actions += 1

# Calculate metrics
non_matching_actions = total_actions - matching_actions
accuracy = matching_actions / total_actions if total_actions > 0 else 0
click_accuracy = matching_click_actions / total_click_actions if total_click_actions > 0 else 0
type_accuracy = matching_type_actions / total_type_actions if total_type_actions > 0 else 0
return_value_accuracy = matching_return_value_actions / total_return_value_actions if total_return_value_actions > 0 else 0
scroll_accuracy = matching_scroll_actions / total_scroll_actions if total_scroll_actions > 0 else 0
micro_recall = (matching_click_actions + matching_type_actions + matching_return_value_actions + matching_scroll_actions) / (total_click_actions + total_type_actions + total_return_value_actions + total_scroll_actions) if (total_click_actions + total_type_actions + total_return_value_actions + total_scroll_actions) > 0 else 0
click_precision = matching_click_actions / total_predicted_click_actions if total_predicted_click_actions > 0 else 0
type_precision = matching_type_actions / total_predicted_type_actions if total_predicted_type_actions > 0 else 0
return_value_precision = matching_return_value_actions / total_predicted_return_value_actions if total_predicted_return_value_actions > 0 else 0
scroll_precision = matching_scroll_actions / total_predicted_scroll_actions if total_predicted_scroll_actions > 0 else 0
micro_precision = (matching_click_actions + matching_type_actions + matching_return_value_actions + matching_scroll_actions) / (total_predicted_click_actions + total_predicted_type_actions + total_predicted_return_value_actions + total_predicted_scroll_actions) if (total_predicted_click_actions + total_predicted_type_actions + total_predicted_return_value_actions + total_predicted_scroll_actions) > 0 else 0
click_f1 = (2 * click_accuracy * click_precision) / (click_accuracy + click_precision) if (click_accuracy + click_precision) > 0 else 0
type_f1 = (2 * type_accuracy * type_precision) / (type_accuracy + type_precision) if (type_accuracy + type_precision) > 0 else 0
return_value_f1 = (2 * return_value_accuracy * return_value_precision) / (return_value_accuracy + return_value_precision) if (return_value_accuracy + return_value_precision) > 0 else 0
scroll_f1 = (2 * scroll_accuracy * scroll_precision) / (scroll_accuracy + scroll_precision) if (scroll_accuracy + scroll_precision) > 0 else 0
micro_f1 = (2 * micro_precision * micro_recall) / (micro_precision + micro_recall) if (micro_precision + micro_recall) > 0 else 0

# Print statistics
print(f"\nTotal number of desired 'Click' actions: {total_click_actions}")
print(f"\nTotal number of predicted 'Click' actions: {total_predicted_click_actions}")
print(f"Number of matching 'Click' actions: {matching_click_actions}")
print(f"'Click' Recall: {click_accuracy:.2%}")
print(f"'Click' Precision: {click_precision:.2%}")
print(f"'Click' F1-Score: {click_f1:.2%}")

print(f"\nTotal number of desired 'Type' actions: {total_type_actions}")
print(f"\nTotal number of predicted 'Type' actions: {total_predicted_type_actions}")
print(f"Number of matching 'Type' actions: {matching_type_actions}")
print(f"'Type' Recall: {type_accuracy:.2%}")
print(f"'Type' Precision: {type_precision:.2%}")
print(f"'Type' F1-Score: {type_f1:.2%}")

print(f"\nTotal number of desired 'Return_value' actions: {total_return_value_actions}")
print(f"\nTotal number of predicted 'Return_value' actions: {total_predicted_return_value_actions}")
print(f"Number of matching 'Return_value' actions: {matching_return_value_actions}")
print(f"'Return_value' Recall: {return_value_accuracy:.2%}")
print(f"'Return_value' Precision: {return_value_precision:.2%}")
print(f"'Return_value' F1-Score: {return_value_f1:.2%}")

print(f"\nTotal number of desired 'Scroll' actions: {total_scroll_actions}")
print(f"\nTotal number of predicted 'Scroll' actions: {total_predicted_scroll_actions}")
print(f"Number of matching 'Scroll' actions: {matching_scroll_actions}")
print(f"'Scroll' Recall: {scroll_accuracy:.2%}")
print(f"'Scroll' Precision: {scroll_precision:.2%}")
print(f"'Scroll' F1-Score: {scroll_f1:.2%}")

print(f"\nTotal number of evaluated actions: {total_actions}")
print(f"\nNumber of matching actions: {matching_actions}")
print(f"Number of non-matching actions: {non_matching_actions}")
print(f"Accuracy: {accuracy:.2%}")
print(f"Micro-averaged Recall: {micro_recall:.2%}")
print(f"Micro-averaged Precision: {micro_precision:.2%}")
print(f"Micro-averaged F1-Score: {micro_f1:.2%}")

print(f"Final results saved at: {output_file}")
