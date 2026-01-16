"""
GitHub Client for Task Health Monitor
Fetches source code files based on stack traces for code-level analysis.
"""
import os
import re
import base64
import requests
from typing import Optional, Dict, List, Any, Tuple


class GitHubClient:
    """Client for querying GitHub API."""
    
    API_BASE = "https://api.github.com"
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub client.
        
        Args:
            token: GitHub personal access token (or from GITHUB_TOKEN env var)
        """
        self.token = token or os.environ.get('GITHUB_TOKEN')
        
        if not self.token:
            raise ValueError("GITHUB_TOKEN not provided")
        
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {self.token}"
        }
    
    def get_file_content(self, owner: str, repo: str, path: str, branch: str = "develop") -> Optional[Dict[str, Any]]:
        """
        Get file content from GitHub repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: Path to file
            branch: Branch name (default: develop)
            
        Returns:
            File content and metadata, or None if not found
        """
        url = f"{self.API_BASE}/repos/{owner}/{repo}/contents/{path}"
        params = {"ref": branch}
        
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 404:
            return None
        
        response.raise_for_status()
        data = response.json()
        
        # Decode content from base64
        content = ""
        if data.get("encoding") == "base64" and data.get("content"):
            content = base64.b64decode(data["content"]).decode("utf-8")
        
        return {
            "path": data.get("path"),
            "name": data.get("name"),
            "sha": data.get("sha"),
            "size": data.get("size"),
            "content": content,
            "html_url": data.get("html_url"),
            "download_url": data.get("download_url")
        }
    
    def search_file(self, owner: str, repo: str, filename: str) -> List[Dict[str, Any]]:
        """
        Search for a file in the repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            filename: Filename to search for
            
        Returns:
            List of matching files
        """
        url = f"{self.API_BASE}/search/code"
        params = {
            "q": f"filename:{filename} repo:{owner}/{repo}"
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        return [
            {
                "path": item.get("path"),
                "name": item.get("name"),
                "html_url": item.get("html_url")
            }
            for item in data.get("items", [])
        ]
    
    def parse_stack_trace(self, stack_trace: str) -> List[Dict[str, Any]]:
        """
        Parse Java stack trace to extract file locations.
        
        Args:
            stack_trace: Java stack trace string
            
        Returns:
            List of parsed stack frames with class name, method, file, and line number
        """
        frames = []
        
        # Pattern for Java stack trace lines
        # at com.example.Class.method(File.java:42)
        pattern = r'at\s+([\w.$]+)\.([\w$<>]+)\(([^:]+):(\d+)\)'
        
        for match in re.finditer(pattern, stack_trace):
            class_name = match.group(1)
            method_name = match.group(2)
            file_name = match.group(3)
            line_number = int(match.group(4))
            
            # Convert class name to file path
            # com.elevva.elevvatecore.repositories.graphql.shopify.orders.GetShopifyOrdersGraphQLRepository
            # -> src/main/java/com/elevva/elevvatecore/repositories/graphql/shopify/orders/GetShopifyOrdersGraphQLRepository.java
            if class_name.startswith("com.elevva.elevvatecore"):
                file_path = "src/main/java/" + class_name.replace(".", "/") + ".java"
                
                frames.append({
                    "class_name": class_name,
                    "method_name": method_name,
                    "file_name": file_name,
                    "file_path": file_path,
                    "line_number": line_number,
                    "is_project_code": True
                })
            else:
                frames.append({
                    "class_name": class_name,
                    "method_name": method_name,
                    "file_name": file_name,
                    "file_path": None,
                    "line_number": line_number,
                    "is_project_code": False
                })
        
        return frames
    
    def get_code_context(
        self, 
        owner: str, 
        repo: str, 
        file_path: str, 
        line_number: int, 
        context_lines: int = 10,
        branch: str = "develop"
    ) -> Optional[Dict[str, Any]]:
        """
        Get code context around a specific line.
        
        Args:
            owner: Repository owner
            repo: Repository name
            file_path: Path to the file
            line_number: Target line number
            context_lines: Number of lines before and after to include
            branch: Branch name
            
        Returns:
            Code context with highlighted target line
        """
        file_data = self.get_file_content(owner, repo, file_path, branch)
        
        if not file_data or not file_data.get("content"):
            return None
        
        lines = file_data["content"].split("\n")
        total_lines = len(lines)
        
        start_line = max(1, line_number - context_lines)
        end_line = min(total_lines, line_number + context_lines)
        
        context_code = []
        for i in range(start_line - 1, end_line):
            line_num = i + 1
            is_target = line_num == line_number
            context_code.append({
                "line_number": line_num,
                "content": lines[i] if i < len(lines) else "",
                "is_target": is_target
            })
        
        return {
            "file_path": file_path,
            "html_url": file_data.get("html_url"),
            "target_line": line_number,
            "start_line": start_line,
            "end_line": end_line,
            "total_lines": total_lines,
            "context": context_code,
            "full_content": file_data["content"]
        }
    
    def get_files_from_stack_trace(
        self,
        owner: str,
        repo: str,
        stack_trace: str,
        max_files: int = 5,
        branch: str = "develop"
    ) -> List[Dict[str, Any]]:
        """
        Get source code for files mentioned in a stack trace.
        
        Args:
            owner: Repository owner
            repo: Repository name
            stack_trace: Java stack trace
            max_files: Maximum number of files to fetch
            branch: Branch name
            
        Returns:
            List of file contents with code context
        """
        frames = self.parse_stack_trace(stack_trace)
        project_frames = [f for f in frames if f.get("is_project_code")]
        
        results = []
        seen_files = set()
        
        for frame in project_frames[:max_files]:
            file_path = frame.get("file_path")
            
            if not file_path or file_path in seen_files:
                continue
            
            seen_files.add(file_path)
            
            code_context = self.get_code_context(
                owner=owner,
                repo=repo,
                file_path=file_path,
                line_number=frame.get("line_number", 1),
                branch=branch
            )
            
            if code_context:
                results.append({
                    "frame": frame,
                    "code": code_context
                })
        
        return results


def get_github_tool_definitions() -> List[Dict[str, Any]]:
    """
    Get Claude tool definitions for GitHub operations.
    These can be passed to Claude API as tools.
    """
    return [
        {
            "name": "github_get_file",
            "description": "Get the content of a specific file from the elevvate-core GitHub repository.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file (e.g., 'src/main/java/com/elevva/elevvatecore/repositories/graphql/shopify/orders/GetShopifyOrdersGraphQLRepository.java')"
                    },
                    "branch": {
                        "type": "string",
                        "description": "Branch name (default: develop)",
                        "default": "develop"
                    }
                },
                "required": ["file_path"]
            }
        },
        {
            "name": "github_get_code_from_stack_trace",
            "description": "Parse a Java stack trace and fetch the source code for the relevant project files. Returns code context around the error lines.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "stack_trace": {
                        "type": "string",
                        "description": "The Java stack trace to analyze"
                    },
                    "max_files": {
                        "type": "integer",
                        "description": "Maximum number of files to fetch (default: 5)",
                        "default": 5
                    },
                    "branch": {
                        "type": "string",
                        "description": "Branch name (default: develop)",
                        "default": "develop"
                    }
                },
                "required": ["stack_trace"]
            }
        },
        {
            "name": "github_get_code_context",
            "description": "Get code context around a specific line in a file. Useful for analyzing a particular location in the codebase.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file"
                    },
                    "line_number": {
                        "type": "integer",
                        "description": "Target line number"
                    },
                    "context_lines": {
                        "type": "integer",
                        "description": "Number of lines before and after to include (default: 10)",
                        "default": 10
                    },
                    "branch": {
                        "type": "string",
                        "description": "Branch name (default: develop)",
                        "default": "develop"
                    }
                },
                "required": ["file_path", "line_number"]
            }
        },
        {
            "name": "github_search_file",
            "description": "Search for a file by name in the elevvate-core repository.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Filename to search for (e.g., 'ShopifyPollingOrdersGraphQLImp.java')"
                    }
                },
                "required": ["filename"]
            }
        }
    ]


def execute_github_tool(
    tool_name: str, 
    tool_input: Dict[str, Any],
    owner: str = "elevva",
    repo: str = "elevvate-core"
) -> Dict[str, Any]:
    """
    Execute a GitHub tool call.
    
    Args:
        tool_name: Name of the tool to execute
        tool_input: Tool input parameters
        owner: Repository owner (default: elevva)
        repo: Repository name (default: elevvate-core)
        
    Returns:
        Tool result
    """
    try:
        client = GitHubClient()
        
        if tool_name == "github_get_file":
            result = client.get_file_content(
                owner=owner,
                repo=repo,
                path=tool_input["file_path"],
                branch=tool_input.get("branch", "develop")
            )
            return {"success": True, "data": result}
        
        elif tool_name == "github_get_code_from_stack_trace":
            result = client.get_files_from_stack_trace(
                owner=owner,
                repo=repo,
                stack_trace=tool_input["stack_trace"],
                max_files=tool_input.get("max_files", 5),
                branch=tool_input.get("branch", "develop")
            )
            return {"success": True, "data": result}
        
        elif tool_name == "github_get_code_context":
            result = client.get_code_context(
                owner=owner,
                repo=repo,
                file_path=tool_input["file_path"],
                line_number=tool_input["line_number"],
                context_lines=tool_input.get("context_lines", 10),
                branch=tool_input.get("branch", "develop")
            )
            return {"success": True, "data": result}
        
        elif tool_name == "github_search_file":
            result = client.search_file(
                owner=owner,
                repo=repo,
                filename=tool_input["filename"]
            )
            return {"success": True, "data": result}
        
        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}
