document.addEventListener('DOMContentLoaded', function() {
    const tabs = document.querySelectorAll('.tab');
    const panels = document.querySelectorAll('.panel');
    const compileBtn = document.getElementById('compileBtn');
    const codeTextarea = document.getElementById('code');
    const statusSpan = document.getElementById('status');
    
    // Tab switching
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active class from all tabs
            tabs.forEach(t => t.classList.remove('active'));
            // Add active class to clicked tab
            tab.classList.add('active');
            
            // Hide all panels
            panels.forEach(p => p.classList.remove('show'));
            // Show the selected panel
            const tabName = tab.getAttribute('data-tab');
            document.getElementById(`panel-${tabName}`).classList.add('show');
        });
    });
    
    // Compile button
    compileBtn.addEventListener('click', compileCode);
    
    function compileCode() {
        const source = codeTextarea.value;
        statusSpan.textContent = 'Compiling...';
        
        fetch('/compile', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ source })
        })
        .then(response => response.json())
        .then(data => {
            statusSpan.textContent = data.success ? 'Success!' : 'Compilation failed';
            displayResults(data);
        })
        .catch(error => {
            statusSpan.textContent = 'Error: ' + error.message;
            console.error('Error:', error);
        });
    }
    
    function displayResults(data) {
        // Display tokens
        const tokensTable = document.getElementById('out-tokens');
        tokensTable.innerHTML = '';
        data.tokens.forEach(token => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${token.type}</td>
                <td>${token.lexeme}</td>
                <td>${token.line}</td>
            `;
            tokensTable.appendChild(row);
        });
        
        // Display symbol table
        const symbolsTable = document.getElementById('out-symbols');
        symbolsTable.innerHTML = '';
        if (data.symbolTable) {
            data.symbolTable.forEach(symbol => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${symbol.name}</td>
                    <td>${symbol.type}</td>
                    <td>${symbol.scope}</td>
                `;
                symbolsTable.appendChild(row);
            });
        }
        
        // Display parse tree
        if (data.parseTree) {
            renderParseTree(data.parseTree);
        }
        
        // Display TAC
        const tacPre = document.getElementById('out-tac');
        tacPre.textContent = data.tac ? data.tac.join('\n') : '';
        
        // Display assembly
        const asmPre = document.getElementById('out-asm');
        asmPre.textContent = data.assembly || '';
        
        // Display errors
        const errorsPre = document.getElementById('out-errors');
        let errorsText = '';
        if (data.errors && data.errors.length > 0) {
            errorsText = data.errors.join('\n');
        }
        errorsPre.textContent = errorsText;
    }
    
    function renderParseTree(treeData) {
        const container = document.getElementById('parse-tree-container');
        container.innerHTML = '';
        
        // Set up the SVG dimensions
        const width = container.clientWidth;
        const height = 600;
        const margin = {top: 20, right: 90, bottom: 30, left: 90};
        
        // Create the SVG
        const svg = d3.select(container)
            .append("svg")
            .attr("width", width)
            .attr("height", height)
            .append("g")
            .attr("transform", `translate(${margin.left},${margin.top})`);
        
        // Create a hierarchy from the tree data
        const root = d3.hierarchy(treeData, d => d.children);
        
        // Tree layout
        const treeLayout = d3.tree().size([width - margin.left - margin.right, height - margin.top - margin.bottom]);
        treeLayout(root);
        
        // Draw the links (edges)
        svg.selectAll(".link")
            .data(root.links())
            .enter()
            .append("path")
            .attr("class", "link")
            .attr("d", d3.linkVertical()
                .x(d => d.x)
                .y(d => d.y))
            .attr("stroke", "#93c5fd")
            .attr("fill", "none");
        
        // Create node groups
        const node = svg.selectAll(".node")
            .data(root.descendants())
            .enter()
            .append("g")
            .attr("class", "node")
            .attr("transform", d => `translate(${d.x},${d.y})`);
        
        // Add circles to nodes
        node.append("circle")
            .attr("r", 10)
            .attr("fill", "#6ee7b7")
            .attr("stroke", "#1f2937")
            .attr("stroke-width", 2);
        
        // Add text labels
        node.append("text")
            .attr("dy", ".35em")
            .attr("y", d => d.children ? -20 : 20)
            .style("text-anchor", "middle")
            .text(d => {
                // Display different properties based on node type
                if (d.data.node === 'Program') return 'Program';
                if (d.data.node === 'DeclList') return 'DeclList';
                if (d.data.node === 'Decl') return `Decl: ${d.data.ids.join(', ')}`;
                if (d.data.node === 'StmtList') return 'StmtList';
                if (d.data.node === 'Assign') return `Assign: ${d.data.id}`;
                if (d.data.node === 'Print') return `Print: ${d.data.id}`;
                if (d.data.node === 'BinOp') return `BinOp: ${d.data.op}`;
                if (d.data.node === 'Num') return `Num: ${d.data.value}`;
                if (d.data.node === 'Var') return `Var: ${d.data.name}`;
                return d.data.node || 'Node';
            })
            .style("fill", "#e5e7eb")
            .style("font-size", "12px");
    }
});