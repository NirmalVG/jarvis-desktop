"""
Jarvis Coding Service
Handles coding and development actions including project creation, code generation, and VS Code setup.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import subprocess
import sys

from brain.product_engineering import product_engineering
from brain.nextjs_expertise import nextjs_expertise
from brain.fastapi_expertise import fastapi_expertise
from brain.coding_buddy import coding_buddy


class CodingService:
    """Service for handling coding and development tasks."""
    
    def __init__(self):
        self.product_engineering = product_engineering
        self.nextjs_expertise = nextjs_expertise
        self.fastapi_expertise = fastapi_expertise
        self.coding_buddy = coding_buddy
    
    def create_project(self, project_type: str, project_name: str, base_path: str = ".") -> Dict[str, str]:
        """
        Create a new project with the specified template.
        
        Args:
            project_type: Type of project (nextjs, fastapi, react_library)
            project_name: Name of the project
            base_path: Base directory where project should be created
            
        Returns:
            Dictionary with creation status and file paths
        """
        project_path = Path(base_path) / project_name
        
        try:
            # Create project directory
            project_path.mkdir(parents=True, exist_ok=True)
            
            if project_type == "nextjs":
                return self._create_nextjs_project(project_name, project_path)
            elif project_type == "fastapi":
                return self._create_fastapi_project(project_name, project_path)
            elif project_type == "react_library":
                return self._create_react_library_project(project_name, project_path)
            else:
                return {
                    "status": "error",
                    "message": f"Unknown project type: {project_type}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to create project: {str(e)}"
            }
    
    def _create_nextjs_project(self, project_name: str, project_path: Path) -> Dict[str, str]:
        """Create a Next.js project."""
        template = self.nextjs_expertise.get_template("fullstack_app")
        if not template:
            return {"status": "error", "message": "Next.js template not found"}
        
        created_files = []
        
        # Create files from template
        for file_path, content in template.files.items():
            full_path = project_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            created_files.append(str(full_path))
        
        # Create additional directories
        (project_path / "components").mkdir(exist_ok=True)
        (project_path / "lib").mkdir(exist_ok=True)
        (project_path / "app" / "api").mkdir(parents=True, exist_ok=True)
        
        return {
            "status": "success",
            "message": f"Next.js project '{project_name}' created successfully",
            "path": str(project_path),
            "files": created_files,
            "setup_commands": template.setup_commands
        }
    
    def _create_fastapi_project(self, project_name: str, project_path: Path) -> Dict[str, str]:
        """Create a FastAPI project."""
        template = self.fastapi_expertise.get_template("microservice")
        if not template:
            return {"status": "error", "message": "FastAPI template not found"}
        
        created_files = []
        
        # Create files from template
        for file_path, content in template.files.items():
            full_path = project_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            created_files.append(str(full_path))
        
        return {
            "status": "success",
            "message": f"FastAPI project '{project_name}' created successfully",
            "path": str(project_path),
            "files": created_files,
            "setup_commands": template.setup_commands
        }
    
    def _create_react_library_project(self, project_name: str, project_path: Path) -> Dict[str, str]:
        """Create a React library project."""
        template = self.coding_buddy.get_template("react_component")
        if not template:
            return {"status": "error", "message": "React library template not found"}
        
        # For now, create a basic structure
        package_json = {
            "name": project_name,
            "version": "0.1.0",
            "description": f"React component library: {project_name}",
            "main": "dist/index.js",
            "module": "dist/index.esm.js",
            "types": "dist/index.d.ts",
            "scripts": {
                "build": "rollup -c",
                "dev": "rollup -c -w",
                "test": "jest",
                "storybook": "start-storybook -p 6006"
            },
            "peerDependencies": {
                "react": ">=16.8.0",
                "react-dom": ">=16.8.0"
            },
            "devDependencies": {
                "@types/react": "^18.0.0",
                "@types/react-dom": "^18.0.0",
                "react": "^18.0.0",
                "react-dom": "^18.0.0",
                "typescript": "^5.0.0",
                "rollup": "^3.0.0",
                "@rollup/plugin-node-resolve": "^15.0.0",
                "@rollup/plugin-typescript": "^11.0.0",
                "jest": "^29.0.0",
                "@testing-library/react": "^13.0.0"
            }
        }
        
        # Create package.json
        with open(project_path / "package.json", 'w') as f:
            json.dump(package_json, f, indent=2)
        
        # Create basic component structure
        src_dir = project_path / "src"
        src_dir.mkdir(exist_ok=True)
        
        # Create index.ts
        with open(src_dir / "index.ts", 'w') as f:
            f.write(f'export {{ default }} from "./{project_name}";\n')
        
        # Create main component
        component_content = template.code.replace("ComponentName", project_name.title())
        with open(src_dir / f"{project_name}.tsx", 'w') as f:
            f.write(component_content)
        
        # Create tsconfig.json
        tsconfig = {
            "compilerOptions": {
                "target": "es5",
                "lib": ["dom", "dom.iterable", "es6"],
                "allowJs": True,
                "skipLibCheck": True,
                "esModuleInterop": True,
                "allowSyntheticDefaultImports": True,
                "strict": True,
                "forceConsistentCasingInFileNames": True,
                "moduleResolution": "node",
                "declaration": True,
                "outDir": "./dist",
                "jsx": "react-jsx"
            },
            "include": ["src"],
            "exclude": ["node_modules", "dist"]
        }
        
        with open(project_path / "tsconfig.json", 'w') as f:
            json.dump(tsconfig, f, indent=2)
        
        return {
            "status": "success",
            "message": f"React library project '{project_name}' created successfully",
            "path": str(project_path),
            "files": [str(project_path / "package.json"), str(src_dir / f"{project_name}.tsx")],
            "setup_commands": template.setup_instructions
        }
    
    def generate_code(self, language: str, template_name: str) -> Dict[str, str]:
        """
        Generate code from a template.
        
        Args:
            language: Programming language (python, typescript, javascript)
            template_name: Name of the template
            
        Returns:
            Dictionary with generated code and metadata
        """
        try:
            if language in ["typescript", "javascript", "tsx", "jsx"]:
                template = self.nextjs_expertise.get_pattern(template_name)
                if template:
                    return {
                        "status": "success",
                        "code": template.code,
                        "description": template.description,
                        "use_case": template.use_case,
                        "language": language
                    }
                
                # Try coding buddy templates
                template = self.coding_buddy.get_template(template_name)
                if template:
                    return {
                        "status": "success",
                        "code": template.code,
                        "description": template.description,
                        "dependencies": template.dependencies,
                        "language": language
                    }
            
            elif language == "python":
                template = self.fastapi_expertise.get_pattern(template_name)
                if template:
                    return {
                        "status": "success",
                        "code": template.code,
                        "description": template.description,
                        "use_case": template.use_case,
                        "language": language
                    }
                
                # Try coding buddy templates
                template = self.coding_buddy.get_template(template_name)
                if template:
                    return {
                        "status": "success",
                        "code": template.code,
                        "description": template.description,
                        "dependencies": template.dependencies,
                        "language": language
                    }
            
            return {
                "status": "error",
                "message": f"Template '{template_name}' not found for language '{language}'"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to generate code: {str(e)}"
            }
    
    def setup_vscode(self, language: str, project_path: str = ".") -> Dict[str, str]:
        """
        Generate VS Code settings and recommendations for a language.
        
        Args:
            language: Programming language
            project_path: Path to the project
            
        Returns:
            Dictionary with settings and file paths
        """
        try:
            vscode_dir = Path(project_path) / ".vscode"
            vscode_dir.mkdir(exist_ok=True)
            
            # Generate settings
            settings = self.coding_buddy.generate_vscode_settings(language)
            
            # Write settings.json
            settings_file = vscode_dir / "settings.json"
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            
            # Generate extensions recommendations
            extensions = []
            for ext_id in self.coding_buddy.list_vscode_extensions():
                ext = self.coding_buddy.get_vscode_extension(ext_id)
                if ext and ext.recommended:
                    extensions.append(ext.id)
            
            # Write extensions.json
            extensions_file = vscode_dir / "extensions.json"
            extensions_recommendations = {
                "recommendations": extensions
            }
            with open(extensions_file, 'w') as f:
                json.dump(extensions_recommendations, f, indent=2)
            
            # Generate launch.json for debugging
            launch_config = self._generate_launch_config(language)
            if launch_config:
                launch_file = vscode_dir / "launch.json"
                with open(launch_file, 'w') as f:
                    json.dump(launch_config, f, indent=2)
            
            return {
                "status": "success",
                "message": f"VS Code setup for {language} completed",
                "files": [str(settings_file), str(extensions_file)],
                "settings": settings,
                "extensions": extensions
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to setup VS Code: {str(e)}"
            }
    
    def _generate_launch_config(self, language: str) -> Optional[Dict]:
        """Generate launch configuration for debugging."""
        if language == "python":
            return {
                "version": "0.2.0",
                "configurations": [
                    {
                        "name": "Python: Current File",
                        "type": "python",
                        "request": "launch",
                        "program": "${file}",
                        "console": "integratedTerminal",
                        "justMyCode": True
                    },
                    {
                        "name": "Python: FastAPI",
                        "type": "python",
                        "request": "launch",
                        "program": "main.py",
                        "console": "integratedTerminal",
                        "justMyCode": True
                    }
                ]
            }
        elif language in ["typescript", "javascript"]:
            return {
                "version": "0.2.0",
                "configurations": [
                    {
                        "name": "Debug Node.js",
                        "type": "node",
                        "request": "launch",
                        "program": "${workspaceFolder}/dist/index.js",
                        "outFiles": ["${workspaceFolder}/dist/**/*.js"]
                    }
                ]
            }
        return None
    
    def get_extension_recommendations(self, category: str = None) -> List[Dict[str, str]]:
        """
        Get VS Code extension recommendations.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of extension dictionaries
        """
        extensions = []
        for ext_id in self.coding_buddy.list_vscode_extensions():
            ext = self.coding_buddy.get_vscode_extension(ext_id)
            if ext and (category is None or ext.category == category):
                extensions.append({
                    "id": ext.id,
                    "name": ext.name,
                    "description": ext.description,
                    "category": ext.category,
                    "recommended": ext.recommended
                })
        
        return extensions
    
    def get_product_engineering_guidance(self, topic: str) -> Dict[str, List[str]]:
        """Get product engineering guidance for a topic."""
        guidance = self.product_engineering.get_guidance(topic)
        if guidance:
            return {
                "best_practices": guidance.best_practices,
                "common_pitfalls": guidance.common_pitfalls,
                "code_examples": guidance.code_examples,
                "resources": guidance.resources
            }
        return {}
    
    def list_available_templates(self, language: str = None) -> Dict[str, List[str]]:
        """List all available templates, optionally filtered by language."""
        templates = {
            "nextjs": self.nextjs_expertise.list_templates(),
            "fastapi": self.fastapi_expertise.list_templates(),
            "coding_buddy": self.coding_buddy.list_templates()
        }
        
        if language:
            # Filter by language if specified
            filtered = {}
            if language in ["typescript", "javascript", "tsx", "jsx"]:
                if "nextjs" in templates:
                    filtered["nextjs"] = templates["nextjs"]
                if "coding_buddy" in templates:
                    filtered["coding_buddy"] = templates["coding_buddy"]
            elif language == "python":
                if "fastapi" in templates:
                    filtered["fastapi"] = templates["fastapi"]
                if "coding_buddy" in templates:
                    filtered["coding_buddy"] = templates["coding_buddy"]
            return filtered
        
        return templates


# Singleton instance
coding_service = CodingService()
