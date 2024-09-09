import json
import os
import string
from typing import Dict, List, Tuple
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from sklearn.manifold import TSNE

def create_co_occurrence_matrix(data_windows: List[List[Tuple[str, str]]]) -> Tuple[np.ndarray, List[str]]:
    all_words = [word.lower().translate(str.maketrans('', '', string.punctuation)).strip() for window in data_windows for word, _ in window]
    unique_words = sorted(list(set(all_words)))
    word_to_index = {word: i for i, word in enumerate(unique_words)}
    matrix = np.ones((len(unique_words), len(unique_words)))
    for window in data_windows:
        words = [word.lower().translate(str.maketrans('', '', string.punctuation)).strip() for word, _ in window]
        for i in range(len(words)):
            for j in range(len(words)):
                if i != j:
                    matrix[word_to_index[words[i]]][word_to_index[words[j]]] += 1
                if i==j:
                    matrix[word_to_index[words[i]]][word_to_index[words[j]]] = 0
    row_sums = matrix.sum(axis=1, keepdims=True)
    probability_matrix = matrix / row_sums
    return probability_matrix, unique_words

def process_startup(startup_data: Dict) -> List[Tuple[str, str]]:
    result = []
    for key, value in startup_data.items():
        if key != "founder_description" and isinstance(value, list):
            result.extend((item['text'], item['label']) for item in value)
    return result

def process_file(file_path: str) -> Dict[str, List[Tuple[str, str]]]:
    with open(file_path, 'r') as file:
        data = json.load(file)
    return {startup: process_startup(startup_data) for startup, startup_data in data.items()}

def generate_graphs(processed_lists):
    create_co_occurrence_matrix(processed_lists)

def create_scatterplots(probability_matrix, unique_words, output_dir, prefix):
    os.makedirs(output_dir, exist_ok=True)
    tsne = TSNE(n_components=2, random_state=42)
    coords = tsne.fit_transform(probability_matrix)
    # plt.figure(figsize=(12, 8))
    # plt.scatter(coords[:, 0], coords[:, 1])
    # for i, word in enumerate(unique_words):
    #     plt.annotate(word, (coords[i, 0], coords[i, 1]))
    # plt.title("("+prefix[0].upper()+prefix[1:]+") Word Co-occurrence Probability (t-SNE)")
    # plt.tight_layout()
    # plt.savefig(os.path.join(output_dir, prefix+"_static_scatterplot.png"))
    # plt.close()
    fig = go.Figure(data=go.Scatter(
        x=coords[:, 0],
        y=coords[:, 1],
        mode='markers',
        text=unique_words,
        hoverinfo='text',
        marker=dict(
            size=8,
            color=np.random.randn(len(unique_words)),
            colorscale='Viridis',
            opacity=0.8
        )
    ))
    fig.update_layout(
        title="("+prefix[0].upper()+prefix[1:]+") Interactive Word Co-occurrence Probability (t-SNE)",
        xaxis_title="t-SNE dimension 1",
        yaxis_title="t-SNE dimension 2",
        hovermode='closest'
    )
    fig.write_html(os.path.join(output_dir, prefix+"_interactive_scatterplot.html"))

if __name__ == "__main__":
    file_path = "startup_ner_records.json"
    processed_data = process_file(os.path.join("data", file_path))
    all_data = [sublist for sublist in processed_data.values()]
    label_data = {label: [[item for item in sublist if item[1] == label] for sublist in processed_data.values()] for label in ["company name", "industry", "problem", "solution", "technology", "audience", "value prop", "key feature", "innovation", "market task", "adjective", "action verb", "person name"]}
    overall_co_occurence_table, overall_vocab = create_co_occurrence_matrix(all_data)
    create_scatterplots(overall_co_occurence_table, overall_vocab, "graphs", "overall")
    for label, list_of_label_ners in label_data.items():
        label_co_occurence_table, label_vocab = create_co_occurrence_matrix(list_of_label_ners)
        create_scatterplots(label_co_occurence_table, label_vocab, "graphs", label)