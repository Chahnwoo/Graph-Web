

let courseCounter = 0;

function addCourse() {
    const courseInput = document.getElementById('courseInput');
    const courseTitle = courseInput.value.toUpperCase().trim();

    if (courseTitle === "") {
        alert("Course ID cannot be empty!");
        return;
    }

    fetch('/check-course-exists', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ courseTitle })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok ' + response.statusText);
        } 
        return response.json();
    })
    .then(data => {
        if (data.exists) {
            console.log('Existing Course ID : ', data.exists)

            const courseContainer = document.getElementById('courseContainer');
        
            const courseBox = document.createElement('div');
            courseBox.className = 'course-box';
            courseBox.id = `courseBox-${courseCounter}`;
            courseBox.innerHTML = `
                <p class="reduced-margin">${courseTitle}</p>
                <button class onclick="removeCourse('${courseCounter}')">Remove</button>
            `;
        
            courseContainer.appendChild(courseBox);
        
            courseCounter++;
            courseInput.value = ""; // Clear the input box
        } else {
            alert("Not a valid Course ID")
        }
    })


}

function removeCourse(courseId) {
    const courseBox = document.getElementById(`courseBox-${courseId}`);
    courseBox.parentNode.removeChild(courseBox);
}

function graphCourses() {
    const courseBoxes = document.querySelectorAll('.course-box');
    const courses = [];

    courseBoxes.forEach(box => {
        courses.push(box.querySelector('p').innerText);
        console.log(box.querySelector('p').innerText)
    });

    fetch('/graph-courses', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ courses })
    })
    .then(response => response.json())
    .then(graphData => {
        visualizeGraph(graphData);
    })
    .catch(error => console.error('Error fetching graph data:', error));

}

function visualizeGraph(graphData) {
    removeGraph()
    // // Clear previous graph
    // d3.select("#graphContainer").selectAll("*").remove();

    // Add nodes to the graph
    let g = new dagreD3.graphlib.Graph().setGraph({});

    graphData.nodes.forEach(node => {
        g.setNode(node.id, {
            'labelStyle' : 'font-weight:bold',
            'shape' : 'circle',
            'width' : 75,
            'height' : 75,
            'name' : node.name,
            'label' : node.label,
            'description' : node.details
        });
    });
    graphData.edges.forEach(edge => {
        g.setEdge(edge.source, edge.target, {
            'arrowhead' : 'vee'
        });
    });

    // Create the renderer
    var render = new dagreD3.render();

    // Set up an SVG group so that we can translate the final graph.
    var svg = d3.select("svg"),
        inner = svg.append("g");

    // Simple function to style the tooltip for the given node.
    var styleTooltip = function(name, description) {
        return "<p class='name'>" + name + "</p><p class='description'>" + description + "</p>";
    };        

    // Run the renderer. This is what draws the final graph.
    render(inner, g);

    inner.selectAll("g.node")
        .attr("title", function(v) { return styleTooltip(v, g.node(v).description) })
        .each(function(v) { $(this).tipsy({ gravity: "w", opacity: 1, html: true }); });
    
    // Resize SVG to fit the container
    const svgWidth = window.innerWidth;
    const svgHeight = window.innerHeight;
    svg.attr("width", svgWidth).attr("height", svgHeight);

    // Center the graph
    const xCenterOffset = (svgWidth - g.graph().width) / 2;
    const yCenterOffset = (svgHeight - g.graph().height) / 2;
    inner.attr("transform", `translate(${xCenterOffset}, ${yCenterOffset})`);

    // Set up zoom behavior
    const zoom = d3.zoom().on("zoom", function(event) {
    inner.attr("transform", event.transform);
    });

    // Apply the zoom behavior to the SVG
    svg.call(zoom);

    // Optional: Set initial zoom level to fit the graph within the SVG container
    const initialScale = Math.min(svgWidth / g.graph().width, svgHeight / g.graph().height);
    const initialTransform = d3.zoomIdentity
    .translate((svgWidth - g.graph().width * initialScale) / 2, (svgHeight - g.graph().height * initialScale) / 2)
    .scale(initialScale);
    svg.call(zoom.transform, initialTransform);
}

function removeGraph() {
    const svg = d3.select('#svg-canvas');
    svg.selectAll('*').remove(); // Remove all child elements of the SVG
}
