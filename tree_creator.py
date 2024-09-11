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

def tree_to_html(tree: Dict[str, Any], title: str, output_dir: str, filename_prefix: str) -> str:
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Arial', sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f4f4f4;
            padding: 20px;
        }}
        #tree-container {{
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 20px;
            max-width: 800px;
            margin: 0 auto;
        }}
        h1 {{
            color: #252c45;
            text-align: center;
            margin-bottom: 20px;
            font-size: 2rem;
        }}
        .description {{
            background-color: #e9f0f7;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
            font-size: 0.9rem;
            line-height: 1.5;
        }}
        .description h2 {{
            color: #252c45;
            margin-top: 0;
            font-size: 1.2rem;
        }}
        .description ul {{
            padding-left: 20px;
            margin-bottom: 10px;
        }}
        .tree-node {{
            margin-left: 20px;
            border-left: 1px solid #ddd;
            padding-left: 15px;
            position: relative;
        }}
        .tree-content {{
            cursor: pointer;
            user-select: none;
            padding: 5px;
            border-radius: 4px;
            transition: background-color 0.3s ease;
        }}
        .tree-content:hover {{
            background-color: #f0f4f7;
        }}
        .tree-content::before {{
            content: '▶';
            color: #1d59d6;
            display: inline-block;
            margin-right: 10px;
            transition: transform 0.3s ease;
        }}
        .tree-content-open::before {{
            transform: rotate(90deg);
        }}
        .tree-children {{
            display: none;
            margin-top: 5px;
        }}
        .tree-children-open {{
            display: block;
            animation: fadeIn 0.5s ease-out;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        .tag {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            margin-right: 5px;
            color: white;
        }}
        .Technology {{ background-color: #3498db; }}
        .Industry {{ background-color: #2ecc71; }}
        .CompanyName {{ background-color: #9b59b6; }}
        .Solution {{ background-color: #e74c3c; }}
        .Audience {{ background-color: #f39c12; }}
        .Problem {{ background-color: #1abc9c; }}
        .ActionVerb {{ background-color: #34495e; }}
        .Innovation {{ background-color: #16a085; }}
        .MarketTask {{ background-color: #2c3e50; }}
        .Adjective {{ background-color: #7f8c8d; }}
        .ValueProp {{ background-color: #8e44ad; }}
        .KeyFeature {{ background-color: #2980b9; }}
        .PersonName {{ background-color: #c0392b; }}
        .percentage {{
            font-size: 0.8em;
            color: #666;
            margin-left: 5px;
        }}
    </style>
</head>
<body>
    <div id="tree-container">
        <h1>YC Startup Pitch Patterns: Analyzing {title} Responses</h1>
        <div class="description">
            <h2>How to Interpret This Tree</h2>
            <p>This tree diagram visualizes the patterns in how AI startups structure their pitch narratives based on an analysis of YCombinator application responses. Each node represents a key element of the pitch, and the percentages show how often that element appears at each level of the narrative structure.</p>
            <ul>
                <li>The top-level elements show what startups tend to lead with in their pitches.</li>
                <li>Child nodes reveal common follow-up elements.</li>
                <li>Percentages indicate the frequency of each pattern.</li>
                <li>The deeper the branch, the more detailed and less common the pattern.</li>
            </ul>
            <p>This analysis helps understand how AI startups typically structure their value propositions and what elements they prioritize when pitching their ideas.</p>
        </div>
        <div class="tree">
"""

    def camel_case(s: str) -> str:
        return ''.join(word.capitalize() for word in s.split(' '))

    def render_tree(node: Dict[str, Any], level: int = 0) -> str:
        tree_html = ""
        for item, data in node.items():
            item_parts = item.split('/')
            item_tags = [camel_case(part) for part in item_parts]
            percentage = data.get("probability", 0) * 100

            tree_html += f'''
            <div class="tree-node">
                <div class="tree-content">
                    {"".join(f'<span class="tag {tag}">{tag}</span>' for tag in item_tags)}
                    <span class="percentage">{percentage:.2f}%</span>
                </div>
                <div class="tree-children">
            '''
            if "children" in data and data["children"]:
                tree_html += render_tree(data["children"], level + 1)
            tree_html += '''
                </div>
            </div>
            '''
        return tree_html

    html += render_tree(tree)

    html += """
        </div>
    </div>
    <script>
        document.querySelectorAll('.tree-content').forEach(node => {
            node.addEventListener('click', function() {
                this.classList.toggle('tree-content-open');
                this.nextElementSibling.classList.toggle('tree-children-open');
            });
        });
    </script>
</body>
</html>
"""

    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{filename_prefix}_tree.html")
    with open(output_file, "w") as f:
        f.write(html)

    return output_file

def print_tree(tree: Dict[str, Any], level: int = 0, prefix: str = "") -> None:
    for item, data in tree.items():
        print(f"{prefix}{item}: {data['probability']:.2%}")
        print_tree(data.get("children", {}), level + 1, prefix + "  ")

def run_tree_creation(target_descriptions, title="Fifty Character Pitch Tree", filename="FiftyCharacter"):
    target_descriptions = [[list(l.values())[1] for l in target_description] for target_description in target_descriptions]
    target_descriptions_tree = build_probability_tree(target_descriptions)
    pruned_target_descriptions_tree = prune_tree(target_descriptions_tree)
    sorted_target_descriptions_tree = recursive_sorted_tree(pruned_target_descriptions_tree)
    print_tree(sorted_target_descriptions_tree)
    output_file = tree_to_html(
        sorted_target_descriptions_tree,
        title+" Pitch Tree",
        "proba_pages",
        filename
    )

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
    all_descriptions = [
        {"title": "Fifty Character", "name": "FiftyCharacter", "data": descriptions},
        {"title": "Description", "name": "Description", "data": descriptions},
        {"title": "Longer TLDR", "name": "LongerTLDR", "data": tldr_one_sentences},
        {"title": "Setting", "name": "Setting", "data": settings},
        {"title": "Solution", "name": "Solution", "data": solutions},
        {"title": "Problem", "name": "Problem", "data": problems},
    ]
    for desc_dict in all_descriptions:
        run_tree_creation(desc_dict["data"], desc_dict["title"], desc_dict["name"])
