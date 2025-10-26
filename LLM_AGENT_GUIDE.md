# LLM Agent Integration Guide

## 🤖 Overview

This guide explains how to integrate this framework with LLM agents to enable autonomous code generation and execution.

## 🎯 Core Capabilities

An LLM agent using this framework can:

1. **Generate Python code** for voxel processing
2. **Compile C++ extensions** for performance-critical operations
3. **Execute code** and capture results
4. **Visualize 3D data** using PyVista
5. **Iterate on errors** until successful
6. **Process images** into 3D volumetric representations

## 🧠 Agent Architecture

### Recommended Agent Design

```
┌─────────────────────────────────────────┐
│         LLM Agent Core                  │
│  (GPT-4, Claude, Llama, etc.)          │
└───────────┬─────────────────────────────┘
            │
            ├─→ Tool: Code Generator
            │   • Uses prompt templates
            │   • Validates syntax
            │
            ├─→ Tool: File Manager
            │   • Creates/edits files
            │   • Manages project structure
            │
            ├─→ Tool: Command Executor
            │   • Runs Python scripts
            │   • Builds C++ extensions
            │   • Captures output/errors
            │
            ├─→ Tool: Validator
            │   • Checks outputs exist
            │   • Verifies data integrity
            │   • Runs tests
            │
            └─→ Tool: Visualizer
                • Generates visualizations
                • Saves images/videos
```

## 📋 Integration Patterns

### Pattern 1: Single Task Execution

**Use Case:** User asks for one specific output

```python
# Example LLM conversation flow:
User: "Create a voxel grid with a sphere and visualize it"

Agent:
  1. Generate code using prompt_templates/code_generation.md
  2. Save as sphere_example.py
  3. Execute: python sphere_example.py
  4. Verify: Check data/sphere.bin exists
  5. Respond with success + show image
```

**Implementation:**
```python
def single_task_agent(user_request):
    # Step 1: Generate code
    code = llm.generate(
        template=load_template("code_generation.md"),
        user_request=user_request
    )
    
    # Step 2: Save to file
    save_file("generated_script.py", code)
    
    # Step 3: Execute
    result = execute("python generated_script.py")
    
    # Step 4: Validate
    if result.success and verify_outputs():
        return "Task completed successfully!"
    else:
        return f"Error: {result.error}"
```

### Pattern 2: Iterative Refinement

**Use Case:** Complex task requiring multiple iterations

```python
def iterative_agent(user_goal):
    max_iterations = 5
    
    for i in range(max_iterations):
        # Generate/modify code
        code = llm.generate_or_fix(
            goal=user_goal,
            previous_error=error if i > 0 else None
        )
        
        # Execute
        result = execute(code)
        
        if result.success:
            return "Success!", result.outputs
        
        # Analyze error and try again
        error = analyze_error(result.stderr)
    
    return "Failed after max iterations"
```

### Pattern 3: Pipeline Construction

**Use Case:** Multi-stage data processing

```python
def pipeline_agent(stages):
    """
    Execute multi-stage pipeline
    
    stages = [
        {"name": "generate", "script": "create_data.py"},
        {"name": "process", "script": "process_data.py"},
        {"name": "visualize", "script": "visualize.py"}
    ]
    """
    results = {}
    
    for stage in stages:
        print(f"Executing stage: {stage['name']}")
        
        # Generate code for this stage if needed
        if "template" in stage:
            code = llm.generate(template=stage["template"])
            save_file(stage["script"], code)
        
        # Execute
        result = execute(f"python {stage['script']}")
        
        if not result.success:
            return f"Failed at stage {stage['name']}: {result.error}"
        
        results[stage["name"]] = result
    
    return "Pipeline completed", results
```

## 🔧 Tool Implementations

### Tool 1: Code Generator

```python
def generate_code(task_description, language="python"):
    """Generate code using LLM with appropriate template."""
    
    # Select template
    if "C++" in task_description or "pybind11" in task_description:
        template_file = "prompt_templates/cpp_module_creation.md"
    else:
        template_file = "prompt_templates/code_generation.md"
    
    template = load_file(template_file)
    
    # Fill template
    prompt = template.format(
        TASK_DESCRIPTION=task_description,
        # ... other parameters
    )
    
    # Generate
    code = llm.complete(prompt)
    
    # Basic validation
    if language == "python":
        validate_python_syntax(code)
    
    return code
```

### Tool 2: Executor with Error Capture

```python
import subprocess
import sys

def execute_python(script_path, timeout=300):
    """Execute Python script and capture output."""
    
    result = {
        "success": False,
        "stdout": "",
        "stderr": "",
        "exit_code": None
    }
    
    try:
        process = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        result["stdout"] = process.stdout
        result["stderr"] = process.stderr
        result["exit_code"] = process.returncode
        result["success"] = (process.returncode == 0)
        
    except subprocess.TimeoutExpired:
        result["stderr"] = f"Execution timeout after {timeout}s"
    except Exception as e:
        result["stderr"] = str(e)
    
    return result
```

### Tool 3: Smart Error Handler

```python
def handle_error(error_message):
    """Analyze error and suggest fixes."""
    
    fixes = []
    
    # Check for common errors
    if "ModuleNotFoundError" in error_message:
        module = extract_module_name(error_message)
        fixes.append({
            "type": "missing_dependency",
            "action": f"pip install {module}",
            "auto_fix": True
        })
    
    elif "FileNotFoundError" in error_message:
        file = extract_filename(error_message)
        fixes.append({
            "type": "missing_file",
            "action": f"Create {file} or check path",
            "auto_fix": False
        })
    
    elif "MemoryError" in error_message:
        fixes.append({
            "type": "out_of_memory",
            "action": "Reduce grid_size or use smaller batch",
            "auto_fix": True,
            "code_modification": "grid_size = 32  # Reduced from 128"
        })
    
    # ... more error patterns
    
    return fixes
```

### Tool 4: Output Validator

```python
def validate_outputs(expected_files):
    """Verify expected output files were created."""
    
    validation_results = {}
    
    for file_path in expected_files:
        result = {
            "exists": os.path.exists(file_path),
            "size": None,
            "valid": False
        }
        
        if result["exists"]:
            result["size"] = os.path.getsize(file_path)
            
            # Check file is not empty or corrupted
            if file_path.endswith(".bin"):
                result["valid"] = validate_voxel_grid(file_path)
            elif file_path.endswith((".png", ".jpg")):
                result["valid"] = validate_image(file_path)
            else:
                result["valid"] = result["size"] > 0
        
        validation_results[file_path] = result
    
    return validation_results

def validate_voxel_grid(bin_file):
    """Check voxel grid is valid."""
    try:
        data = np.fromfile(bin_file, dtype=np.float32)
        
        # Check size makes sense (should be N^3 for some N)
        size = len(data)
        n = round(size ** (1/3))
        
        if n ** 3 != size:
            return False
        
        # Check values are reasonable
        if np.all(data == 0):
            return False  # All zeros - probably error
        
        if np.any(np.isnan(data)) or np.any(np.isinf(data)):
            return False  # Contains NaN or Inf
        
        return True
    except:
        return False
```

## 📊 Example LLM Agent Session

```
User: I want to create a 3D voxel representation of the letter "A"

Agent: I'll help you create a voxel grid with the letter "A". Let me break this down:
       1. Generate voxel grid with "A" pattern
       2. Save to binary file
       3. Visualize the result

[Agent generates code using template...]

Agent: Created script: create_letter_a.py
       Executing...

[Executes Python script...]

Agent: ✓ Script completed successfully
       ✓ Created: data/letter_a.bin (64×64×64 voxels)
       ✓ Non-zero voxels: 2,347
       
       Now visualizing...

[Executes visualization...]

Agent: ✓ Visualization complete
       📊 Output saved to: output/letter_a.png
       
       [Shows image]
       
       Would you like me to modify the pattern or create additional letters?

User: Make it bigger and rotate it 45 degrees

Agent: I'll modify the voxel grid to be larger and apply rotation.
       Updating grid size from 64 to 128...
       Applying 45° rotation around Z-axis...
       
[Agent modifies existing code and re-runs...]

Agent: ✓ Updated voxel grid created
       📊 New file: data/letter_a_rotated.bin (128×128×128)
       [Shows rotated image]
       
       The letter A is now 2x larger and rotated 45°.
```

## 🚀 Advanced Features

### Feature 1: Automatic C++ Extension Generation

```python
def generate_cpp_extension(function_spec):
    """Generate and compile C++ extension on-the-fly."""
    
    # Generate C++ code
    cpp_code = llm.generate(
        template=load_template("cpp_module_creation.md"),
        spec=function_spec
    )
    
    # Save
    save_file("generated_module.cpp", cpp_code)
    
    # Update setup.py
    update_setup_py("generated_module")
    
    # Compile
    result = execute("python setup.py build_ext --inplace")
    
    if result.success:
        return True, "generated_module"
    else:
        return False, result.stderr
```

### Feature 2: Benchmark-Driven Optimization

```python
def optimize_for_performance(script_path):
    """Automatically optimize code for performance."""
    
    # Baseline
    baseline_time = benchmark(script_path)
    
    optimizations = [
        "vectorize_loops",
        "use_cpp_extension",
        "parallelize",
        "reduce_precision"
    ]
    
    best_time = baseline_time
    best_version = script_path
    
    for opt in optimizations:
        # Apply optimization
        optimized_code = llm.optimize(
            load_file(script_path),
            optimization=opt
        )
        
        # Save and test
        test_path = f"optimized_{opt}.py"
        save_file(test_path, optimized_code)
        
        time = benchmark(test_path)
        
        if time < best_time:
            best_time = time
            best_version = test_path
    
    speedup = baseline_time / best_time
    return best_version, speedup
```

### Feature 3: Interactive Debugging

```python
def debug_with_llm(script_path, error):
    """Interactively debug with LLM assistance."""
    
    # Get code context
    code = load_file(script_path)
    
    # Ask LLM to analyze
    analysis = llm.analyze_error(
        code=code,
        error=error,
        template=load_template("execution_prompts.md")
    )
    
    print(f"Error analysis: {analysis}")
    
    # Get proposed fixes
    fixes = analysis["proposed_fixes"]
    
    for i, fix in enumerate(fixes):
        print(f"\nTrying fix {i+1}: {fix['description']}")
        
        # Apply fix
        fixed_code = apply_fix(code, fix)
        save_file(script_path, fixed_code)
        
        # Test
        result = execute(f"python {script_path}")
        
        if result.success:
            print("✓ Fix successful!")
            return True
    
    print("❌ All fixes failed")
    return False
```

## 📈 Performance Considerations

### When to Use C++ Extensions

```python
def should_use_cpp(operation):
    """Decide if C++ extension is worthwhile."""
    
    use_cpp_if = [
        operation["grid_size"] > 64,  # Large grids
        operation["type"] in ["ray_casting", "convolution"],  # Compute-intensive
        operation["repeat_count"] > 10,  # Repeated operations
    ]
    
    return any(use_cpp_if)
```

### Resource Management

```python
def estimate_memory(grid_size):
    """Estimate memory requirements."""
    
    # float32 = 4 bytes
    voxels = grid_size ** 3
    bytes_needed = voxels * 4
    
    # Add overhead
    total = bytes_needed * 1.5
    
    return {
        "voxels": voxels,
        "bytes": total,
        "mb": total / (1024**2),
        "gb": total / (1024**3)
    }
```

## 🎓 Best Practices

1. **Always validate generated code** before execution
2. **Use sandboxing** for untrusted code
3. **Set timeouts** on all executions
4. **Capture and log** all outputs
5. **Provide helpful error messages** to users
6. **Save intermediate results** for debugging
7. **Use version control** for generated code
8. **Test with small datasets** first
9. **Monitor resource usage** (CPU, memory, disk)
10. **Document** what the agent did

## 📝 License

This framework is designed to be used with various LLM agents including commercial and open-source models.



