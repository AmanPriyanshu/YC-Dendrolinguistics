from collections import defaultdict
from typing import List, Dict, Any
import json
import os
from tqdm import tqdm
from collections import OrderedDict

def build_probability_tree(data: List[List[str]]) -> Dict[str, Any]:
    tree = {}
    for path in data:
        current = tree
        for item in path:
            if item not in current:
                current[item] = {"count": 1, "children": {}}
            else:
                current[item]["count"] += 1
            current = current[item]["children"]

    def calculate_probabilities(node: Dict[str, Any]) -> None:
        for item, item_data in node.items():
            item_data["probability"] = item_data["count"] / len(data)
            calculate_probabilities(item_data["children"])

    calculate_probabilities(tree)
    return tree

def prune_tree(node: Dict[str, Any], threshold: float = 0.01) -> Dict[str, Any]:
    pruned = {}
    low_prob_items = []
    low_prob_sum = 0

    for item, data in node.items():
        if data["probability"] < threshold:
            low_prob_items.append(item)
            low_prob_sum += data["probability"]
        else:
            pruned[item] = data
            pruned[item]["children"] = prune_tree(data["children"], threshold)

    if low_prob_items:
        if all(node[item]["probability"] < threshold for item in low_prob_items):
            collapsed_key = "/".join(low_prob_items)
            pruned[collapsed_key] = {
                "probability": low_prob_sum,
                "children": {}
            }
        else:
            for item in low_prob_items:
                pruned[item] = node[item]
                pruned[item]["children"] = prune_tree(node[item]["children"], threshold)

    return pruned

def recursive_sorted_tree(node: Dict[str, Any]) -> OrderedDict:
    sorted_node = OrderedDict(sorted(node.items(), key=lambda x: x[1]["probability"], reverse=True))
    for item, data in sorted_node.items():
        if "children" in data and data["children"]:
            data["children"] = recursive_sorted_tree(data["children"])
    return sorted_node

def print_tree(tree: Dict[str, Any], level: int = 0, prefix: str = "") -> None:
    for item, data in tree.items():
        print(f"{prefix}{item}: {data['probability']:.2%}")
        print_tree(data.get("children", {}), level + 1, prefix + "  ")

if __name__=='__main__':
    with open(os.path.join("data", "startup_ner_records.json"), "r") as f:
        data = json.load(f)
    short_descriptions = []
    descriptions = []
    tldr_one_sentences = []
    settings = []
    problems = []
    solutions = []
    for startup_name, startup in tqdm(data.items(), total=len(list(data.keys()))):
        short_description = startup.get('short_description')
        description = startup.get('description')
        tldr_one_sentence = startup.get('tldr_one_sentence')
        setting = startup.get('setting')
        problem = startup.get('problem')
        solution = startup.get('solution')
        if short_description is not None and len(short_description)>0:
            short_descriptions.append(short_description)
        if description is not None and len(description)>0:
            descriptions.append(description)
        if tldr_one_sentence is not None and len(tldr_one_sentence)>0:
            tldr_one_sentences.append(tldr_one_sentence)
        if setting is not None and len(setting)>0:
            settings.append(setting)
        if problem is not None and len(problem)>0:
            problems.append(problem)
        if solution is not None and len(solution)>0:
            solutions.append(solution)
    short_descriptions = [[list(l.values())[1] for l in short_description] for short_description in short_descriptions]
    short_descriptions_tree = build_probability_tree(short_descriptions)
    pruned_short_descriptions_tree = prune_tree(short_descriptions_tree)
    sorted_short_descriptions_tree = recursive_sorted_tree(pruned_short_descriptions_tree)
    print_tree(sorted_short_descriptions_tree)