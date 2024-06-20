from flask import Flask, request, jsonify, render_template
from course_lookup import *
from course_lookup import _process_forbidden_overlaps
import networkx as nx

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/plan')
def plan():
    return render_template('plan.html')

@app.route('/submit', methods=['POST'])
def submit_data():
    graph_input = request.form['graph-input']  # Retrieve input data from form
    course_data= get_course_details(base_str_to_course(graph_input))

    prereq_tree = { graph_input.upper() : course_data }

    G = nx.DiGraph()
    def get_data(prereq_tree):
        course_nodes = set()
        course_edges = set()

        for course_id, details in prereq_tree.items():
            course_nodes.add(course_id)
            course_edges.update([f"{prereq_node}-{course_id}" for prereq_node in details['prereq_tree'].keys()])
            prereq_nodes, prereq_edges = get_data(details['prereq_tree'])
            course_nodes.update(prereq_nodes)
            course_edges.update(prereq_edges)
            
        return course_nodes, course_edges
        
    nodes, edges = get_data(prereq_tree)
    edges = [tuple(edge.split('-')) for edge in sorted(edges)]
    
    graph = dag_from_ne(sorted(nodes), edges)

    returned_data = {
        "nodes" : [{'id' : node, 'label' : node, 'name' : graph.nodes[node].get('name'), 'details' : graph.nodes[node].get('description')}  for node in graph.nodes()],
        "edges" : [{'source' : u, 'target' : v} for u, v in graph.edges()]
    }
    return jsonify(returned_data)

@app.route('/graph-courses', methods=['POST'])
def graph_courses():
    data = request.get_json()
    courses = data.get('courses', [])

    print(type(courses[0]))

    nodes, edges = courses_as_graph([base_str_to_course(course_text) for course_text in courses])
    graph = dag_from_ne(nodes, edges)

    returned_data = {
        "nodes" : [{'id' : node, 'label' : node, 'name' : graph.nodes[node].get('name'), 'details' : graph.nodes[node].get('description')}  for node in graph.nodes()],
        "edges" : [{'source' : u, 'target' : v} for u, v in graph.edges()]
    }
    return jsonify(returned_data)

if __name__ == '__main__':
    app.run(debug=True)