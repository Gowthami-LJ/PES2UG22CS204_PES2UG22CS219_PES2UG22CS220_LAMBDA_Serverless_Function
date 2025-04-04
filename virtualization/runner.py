import subprocess
import sys
import os

def run_in_docker(code, language, timeout):
    # Create a temporary directory for building the Docker image
    temp_dir = f"temp_{language}_{hash(code)}"
    os.makedirs(temp_dir, exist_ok=True)
    
    # Create the appropriate file based on language
    if language.lower() == "python":
        dockerfile = "Dockerfile.python"
        code_file = os.path.join(temp_dir, "function.py")
    elif language.lower() == "javascript":
        dockerfile = "Dockerfile.javascript"
        code_file = os.path.join(temp_dir, "function.js")
    else:
        return {"error": f"Unsupported language: {language}"}
    
    # Write the code to the file
    with open(code_file, "w") as f:
        f.write(code)
    
    # Copy the appropriate Dockerfile
    with open(f"virtualization/{dockerfile}", "r") as src, open(os.path.join(temp_dir, "Dockerfile"), "w") as dst:
        dst.write(src.read())
    
    # Build the image
    image_name = f"{language.lower()}_function_{hash(code)}"
    try:
        subprocess.run(
            ["docker", "build", "-t", image_name, temp_dir],
            check=True, capture_output=True, text=True
        )
        
        # Run the container
        result = subprocess.run(
            ["docker", "run", "--rm", image_name],
            capture_output=True, text=True,
            timeout=timeout
        )
        
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"error": "Execution timed out!"}
    except subprocess.CalledProcessError as e:
        return {"error": f"Docker error: {e.output}"}
    finally:
        # Clean up
        subprocess.run(["docker", "rmi", "-f", image_name], capture_output=True)
        import shutil
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    # Example usage
    js_code = "console.log('Hello from JavaScript!');"
    py_code = "print('Hello from Python!')"
    
    print("Running JavaScript function:")
    print(run_in_docker(js_code, "javascript", 5))
    
    print("Running Python function:")
    print(run_in_docker(py_code, "python", 5))
