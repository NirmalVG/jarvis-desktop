"""
Jarvis Coding Buddy Module
Enhanced coding assistance for VS Code and general development workflows.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import re
import os
import json


@dataclass
class CodeTemplate:
    name: str
    language: str
    description: str
    code: str
    dependencies: List[str]
    setup_instructions: List[str]


@dataclass
class VSCodeExtension:
    name: str
    id: str
    description: str
    category: str
    recommended: bool


class CodingBuddy:
    """Enhanced coding buddy with VS Code integration and project scaffolding."""
    
    def __init__(self):
        self.templates = self._build_templates()
        self.vscode_extensions = self._build_vscode_extensions()
        self.snippets = self._build_snippets()
        self.project_wizards = self._build_project_wizards()
    
    def _build_templates(self) -> Dict[str, CodeTemplate]:
        """Build code templates for various languages and frameworks."""
        
        return {
            "react_component": CodeTemplate(
                name="React Functional Component",
                language="TypeScript",
                description="Modern React component with TypeScript and hooks",
                code='''import React, { useState, useEffect } from 'react';

interface Props {
  // Define your props here
  title: string;
  onAction?: () => void;
}

const ComponentName: React.FC<Props> = ({ title, onAction }) => {
  const [state, setState] = useState<string>('');
  
  useEffect(() => {
    // Side effects here
    console.log('Component mounted');
  }, []);

  const handleClick = () => {
    // Handle click
    if (onAction) {
      onAction();
    }
  };

  return (
    <div className="component-name">
      <h1>{title}</h1>
      <button onClick={handleClick}>
        Click me
      </button>
    </div>
  );
};

export default ComponentName;''',
                dependencies=["react", "@types/react"],
                setup_instructions=[
                    "npx create-react-app my-app --template typescript",
                    "cd my-app",
                    "npm install"
                ]
            ),
            
            "fastapi_endpoint": CodeTemplate(
                name="FastAPI Endpoint",
                language="Python",
                description="Production-ready FastAPI endpoint with validation",
                code='''from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.auth import get_current_user
from app.schemas.item import ItemCreate, ItemResponse, ItemUpdate
from app.services.item_service import ItemService

router = APIRouter()

@router.get("/", response_model=List[ItemResponse])
async def get_items(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all items with pagination."""
    item_service = ItemService(db)
    return await item_service.get_items(skip=skip, limit=limit)

@router.post("/", response_model=ItemResponse)
async def create_item(
    item: ItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new item."""
    item_service = ItemService(db)
    return await item_service.create_item(item, current_user.id)

@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific item by ID."""
    item_service = ItemService(db)
    item = await item_service.get_item(item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    return item

@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int,
    item_update: ItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing item."""
    item_service = ItemService(db)
    item = await item_service.update_item(item_id, item_update)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    return item

@router.delete("/{item_id}")
async def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an item."""
    item_service = ItemService(db)
    success = await item_service.delete_item(item_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    return {"message": "Item deleted successfully"}''',
                dependencies=["fastapi", "sqlalchemy", "pydantic"],
                setup_instructions=[
                    "pip install fastapi uvicorn sqlalchemy pydantic",
                    "Create the necessary service and schema files"
                ]
            ),
            
            "nextjs_page": CodeTemplate(
                name="Next.js Page",
                language="TypeScript",
                description="Next.js page with data fetching and metadata",
                code='''import { GetServerSideProps, GetStaticProps, NextPage } from 'next';
import Head from 'next/head';
import { useState, useEffect } from 'react';

interface PageProps {
  data?: any;
  error?: string;
}

const PageName: NextPage<PageProps> = ({ data, error }) => {
  const [localState, setLocalState] = useState<string>('');

  useEffect(() => {
    // Client-side effects
    console.log('Page loaded');
  }, []);

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <>
      <Head>
        <title>Page Title - My App</title>
        <meta name="description" content="Page description" />
        <meta property="og:title" content="Page Title" />
        <meta property="og:description" content="Page description" />
      </Head>
      
      <main className="container">
        <h1>Page Title</h1>
        
        {data && (
          <div className="data-section">
            {/* Render your data here */}
            <pre>{JSON.stringify(data, null, 2)}</pre>
          </div>
        )}
        
        <div className="interactive-section">
          <input
            type="text"
            value={localState}
            onChange={(e) => setLocalState(e.target.value)}
            placeholder="Enter something..."
          />
          <p>You typed: {localState}</p>
        </div>
      </main>
      
      <style jsx>{`
        .container {
          max-width: 1200px;
          margin: 0 auto;
          padding: 2rem;
        }
        
        .data-section {
          margin: 2rem 0;
          padding: 1rem;
          background: #f5f5f5;
          border-radius: 8px;
        }
        
        .interactive-section {
          margin: 2rem 0;
        }
        
        input {
          padding: 0.5rem;
          border: 1px solid #ccc;
          border-radius: 4px;
          margin-right: 1rem;
        }
      `}</style>
    </>
  );
};

// Server-side data fetching
export const getServerSideProps: GetServerSideProps = async (context) => {
  try {
    // Fetch data from API or database
    const data = await fetch('https://api.example.com/data').then(res => res.json());
    
    return {
      props: {
        data,
      },
    };
  } catch (error) {
    return {
      props: {
        error: 'Failed to fetch data',
      },
    };
  }
};

// Or static generation
// export const getStaticProps: GetStaticProps = async () => {
//   // Fetch data at build time
//   return {
//     props: {
//       data: [],
//     },
//   };
// };

export default PageName;''',
                dependencies=["next", "react", "@types/react"],
                setup_instructions=[
                    "npx create-next-app@latest my-app --typescript",
                    "cd my-app",
                    "npm install"
                ]
            ),
            
            "python_class": CodeTemplate(
                name="Python Class",
                language="Python",
                description="Well-structured Python class with type hints and docstrings",
                code='''from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

@dataclass
class ModelConfig:
    """Configuration for the model."""
    param1: str
    param2: int = 10
    param3: Optional[float] = None

class ModelClass:
    """
    A well-structured Python class with proper documentation.
    
    Attributes:
        config (ModelConfig): Configuration object
        _internal_state (Dict[str, Any]): Internal state storage
    """
    
    def __init__(self, config: ModelConfig):
        """
        Initialize the ModelClass.
        
        Args:
            config: Configuration object containing model parameters
        """
        self.config = config
        self._internal_state: Dict[str, Any] = {}
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize internal state."""
        self._internal_state = {
            'initialized': True,
            'created_at': datetime.now().isoformat(),
        }
        logger.info(f"Model initialized with config: {self.config}")
    
    def process_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process input data and return results.
        
        Args:
            data: List of dictionaries containing input data
            
        Returns:
            List of processed data dictionaries
            
        Raises:
            ValueError: If data format is invalid
        """
        if not isinstance(data, list):
            raise ValueError("Data must be a list")
        
        processed_data = []
        for item in data:
            try:
                processed_item = self._process_single_item(item)
                processed_data.append(processed_item)
            except Exception as e:
                logger.error(f"Error processing item {item}: {e}")
                raise
        
        return processed_data
    
    def _process_single_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single data item."""
        # Add your processing logic here
        return {
            'original': item,
            'processed': True,
            'config_param1': self.config.param1,
            'config_param2': self.config.param2,
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the model."""
        return {
            'config': self.config,
            'internal_state': self._internal_state,
            'is_initialized': self._internal_state.get('initialized', False),
        }
    
    def __str__(self) -> str:
        """String representation of the model."""
        return f"ModelClass(config={self.config})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the model."""
        return f"ModelClass(config={self.config}, state={self._internal_state})"


# Example usage
if __name__ == "__main__":
    config = ModelConfig(param1="example", param2=20)
    model = ModelClass(config)
    
    sample_data = [
        {"id": 1, "value": "test1"},
        {"id": 2, "value": "test2"},
    ]
    
    try:
        results = model.process_data(sample_data)
        print(f"Processed {len(results)} items")
        print(f"Model status: {model.get_status()}")
    except Exception as e:
        print(f"Error: {e}")''',
                dependencies=["dataclasses", "typing", "logging"],
                setup_instructions=[
                    "No additional dependencies needed",
                    "Just copy the code into your Python file"
                ]
            )
        }
    
    def _build_vscode_extensions(self) -> Dict[str, VSCodeExtension]:
        """Build recommended VS Code extensions."""
        
        return {
            "python": VSCodeExtension(
                name="Python",
                id="ms-python.python",
                description="Official Python extension with IntelliSense, debugging, and more",
                category="Languages",
                recommended=True
            ),
            "prettier": VSCodeExtension(
                name="Prettier - Code formatter",
                id="esbenp.prettier-vscode",
                description="Code formatter for JavaScript, TypeScript, and more",
                category="Formatters",
                recommended=True
            ),
            "eslint": VSCodeExtension(
                name="ESLint",
                id="dbaeumer.vscode-eslint",
                description="Integrates ESLint into VS Code",
                category="Linters",
                recommended=True
            ),
            "gitlens": VSCodeExtension(
                name="GitLens — Git supercharged",
                id="eamodio.gitlens",
                description="Supercharge Git capabilities in VS Code",
                category="Git",
                recommended=True
            ),
            "docker": VSCodeExtension(
                name="Docker",
                id="ms-azuretools.vscode-docker",
                description="Manage Docker containers and images",
                category="DevOps",
                recommended=True
            ),
            "thunderclient": VSCodeExtension(
                name="Thunder Client",
                id="rangav.vscode-thunder-client",
                description="REST API client for testing APIs",
                category="Testing",
                recommended=True
            ),
            "autopep8": VSCodeExtension(
                name="autopep8",
                id="ms-python.autopep8",
                description="Python code formatter using autopep8",
                category="Formatters",
                recommended=True
            ),
            "black": VSCodeExtension(
                name="Black Formatter",
                id="ms-python.black-formatter",
                description="Python code formatter using Black",
                category="Formatters",
                recommended=True
            ),
            "mypy": VSCodeExtension(
                name="Mypy Type Checker",
                id="ms-python.mypy-type-checker",
                description="Type checking for Python using mypy",
                category="Linters",
                recommended=True
            ),
            "tailwindcss": VSCodeExtension(
                name="Tailwind CSS IntelliSense",
                id="bradlc.vscode-tailwindcss",
                description="Intelligent Tailwind CSS tooling",
                category="CSS",
                recommended=True
            )
        }
    
    def _build_snippets(self) -> Dict[str, Dict[str, str]]:
        """Build code snippets for various languages."""
        
        return {
            "javascript": {
                "react_functional_component": '''import React, { useState } from 'react';

const ${1:ComponentName} = () => {
  const [${2:state}, set${2/(.*)/${1:/capitalize}/}] = useState(${3:initialValue});

  return (
    <div className="${1:ComponentName}">
      <h1>${4:Title}</h1>
    </div>
  );
};

export default ${1:ComponentName};''',
                
                "async_function": '''const ${1:functionName} = async (${2:params}) => {
  try {
    const result = await ${3:asyncOperation};
    return result;
  } catch (error) {
    console.error('Error in ${1:functionName}:', error);
    throw error;
  }
};''',
                
                "api_call": '''const ${1:fetchData} = async () => {
  try {
    const response = await fetch('${2:url}', {
      method: '${3:GET}',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error('HTTP error! status: ${response.status}');
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching data:', error);
    throw error;
  }
};'''
            },
            
            "python": {
                "async_function": '''async def ${1:function_name}(${2:params}):
    """
    ${3:Description of the function}
    
    Args:
        ${2:params}: ${4:Parameter description}
    
    Returns:
        ${5:Return value description}
    
    Raises:
        ${6:Exception}: ${7:Exception description}
    """
    try:
        result = await ${8:async_operation}
        return result
    except Exception as e:
        logger.error(f"Error in ${1:function_name}: {e}")
        raise''',
                
                "class_definition": '''class ${1:ClassName}:
    """
    ${2:Description of the class}
    
    Attributes:
        ${3:attribute1}: ${4:Attribute description}
    """
    
    def __init__(self, ${5:params}):
        """
        Initialize ${1:ClassName}.
        
        Args:
            ${5:params}: ${6:Parameter description}
        """
        ${7:self.attribute1 = ${8:value}}
    
    def ${9:method_name}(self, ${10:params}):
        """
        ${11:Method description}
        
        Args:
            ${10:params}: ${12:Parameter description}
        
        Returns:
            ${13:Return value description}
        """
        ${14:pass}''',
                
                "fastapi_endpoint": '''@router.${1:get}("${2:path}", response_model=${3:ResponseModel})
async def ${4:function_name}(
    ${5:param}: ${6:Type} = ${7:Default},
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    ${8:Endpoint description}
    
    Args:
        ${5:param}: ${9:Parameter description}
        db: Database session
        current_user: Authenticated user
    
    Returns:
        ${10:Return value description}
    """
    ${11:pass}'''
            },
            
            "typescript": {
                "interface_definition": '''interface ${1:InterfaceName} {
    ${2:property}: ${3:string};
    ${4:optional_property}?: ${5:number};
    ${6:method}(): ${7:void};
}''',
                
                "type_definition": '''type ${1:TypeName} = {
    ${2:property}: ${3:string};
    ${4:optional_property}?: ${5:number};
} | ${6:AlternativeType};''',
                
                "react_hook": '''const ${1:useCustomHook} = (${2:params}) => {
    const [${3:state}, set${3/(.*)/${1:/capitalize}/}] = useState<${4:Type}>(${5:initialValue});
    
    useEffect(() => {
        ${6:// Effect logic}
    }, [${7:dependencies}]);
    
    const ${8:action} = useCallback(() => {
        ${9:// Action logic}
    }, [${10:dependencies}]);
    
    return {
        ${3:state},
        ${8:action},
    };
};'''
            }
        }
    
    def _build_project_wizards(self) -> Dict[str, Dict[str, any]]:
        """Build project setup wizards."""
        
        return {
            "next_fullstack": {
                "name": "Next.js Full-Stack App",
                "description": "Complete Next.js application with authentication, database, and API",
                "steps": [
                    {
                        "title": "Initialize Next.js Project",
                        "command": "npx create-next-app@latest {project_name} --typescript --tailwind --eslint --app",
                        "description": "Create a new Next.js project with TypeScript and Tailwind CSS"
                    },
                    {
                        "title": "Install Dependencies",
                        "command": "cd {project_name} && npm install @prisma/client prisma next-auth bcryptjs @types/bcryptjs",
                        "description": "Install database and authentication dependencies"
                    },
                    {
                        "title": "Initialize Prisma",
                        "command": "cd {project_name} && npx prisma init",
                        "description": "Initialize Prisma for database management"
                    },
                    {
                        "title": "Setup Environment",
                        "command": "cd {project_name} && cp .env.local.example .env.local",
                        "description": "Setup environment variables"
                    }
                ]
            },
            
            "fastapi_microservice": {
                "name": "FastAPI Microservice",
                "description": "Production-ready FastAPI microservice with authentication and database",
                "steps": [
                    {
                        "title": "Create Project Structure",
                        "command": "mkdir -p {project_name}/{app,tests} && cd {project_name}",
                        "description": "Create project directory structure"
                    },
                    {
                        "title": "Create Virtual Environment",
                        "command": "python -m venv venv && source venv/bin/activate",
                        "description": "Create and activate virtual environment"
                    },
                    {
                        "title": "Install Dependencies",
                        "command": "pip install fastapi uvicorn sqlalchemy alembic pydantic python-jose passlib",
                        "description": "Install FastAPI and dependencies"
                    },
                    {
                        "title": "Setup Project Files",
                        "command": "# Create main.py, requirements.txt, and other project files",
                        "description": "Create initial project files"
                    }
                ]
            },
            
            "react_library": {
                "name": "React Component Library",
                "description": "Reusable React component library with TypeScript and Storybook",
                "steps": [
                    {
                        "title": "Initialize Project",
                        "command": "npx create-react-library {project_name} --template typescript",
                        "description": "Create a new React library project"
                    },
                    {
                        "title": "Install Storybook",
                        "command": "cd {project_name} && npx storybook@latest init",
                        "description": "Initialize Storybook for component documentation"
                    },
                    {
                        "title": "Setup Testing",
                        "command": "cd {project_name} && npm install --save-dev @testing-library/react @testing-library/jest-dom",
                        "description": "Install testing dependencies"
                    }
                ]
            }
        }
    
    def get_template(self, template_name: str) -> Optional[CodeTemplate]:
        """Get a specific code template."""
        return self.templates.get(template_name)
    
    def get_vscode_extension(self, extension_id: str) -> Optional[VSCodeExtension]:
        """Get a specific VS Code extension."""
        return self.vscode_extensions.get(extension_id)
    
    def get_snippet(self, language: str, snippet_name: str) -> Optional[str]:
        """Get a specific code snippet."""
        return self.snippets.get(language, {}).get(snippet_name)
    
    def get_project_wizard(self, wizard_name: str) -> Optional[Dict[str, any]]:
        """Get a specific project wizard."""
        return self.project_wizards.get(wizard_name)
    
    def list_templates(self) -> List[str]:
        """List all available templates."""
        return list(self.templates.keys())
    
    def list_vscode_extensions(self) -> List[str]:
        """List all VS Code extensions."""
        return list(self.vscode_extensions.keys())
    
    def list_snippets(self, language: str) -> List[str]:
        """List snippets for a specific language."""
        return list(self.snippets.get(language, {}).keys())
    
    def list_project_wizards(self) -> List[str]:
        """List all project wizards."""
        return list(self.project_wizards.keys())
    
    def generate_vscode_settings(self, language: str) -> Dict[str, any]:
        """Generate VS Code settings for a specific language."""
        
        settings = {
            "editor.formatOnSave": True,
            "editor.codeActionsOnSave": {
                "source.fixAll.eslint": "explicit",
                "source.organizeImports": "explicit"
            },
            "files.exclude": {
                "**/__pycache__": True,
                "**/node_modules": True,
                "**/.git": True,
                "**/.DS_Store": True
            }
        }
        
        if language == "python":
            settings.update({
                "python.defaultInterpreterPath": "./venv/bin/python",
                "python.formatting.provider": "black",
                "python.linting.enabled": True,
                "python.linting.pylintEnabled": False,
                "python.linting.mypyEnabled": True,
                "python.testing.pytestEnabled": True,
                "python.testing.unittestEnabled": False
            })
        elif language == "javascript" or language == "typescript":
            settings.update({
                "typescript.preferences.importModuleSpecifier": "relative",
                "eslint.workingDirectories": ["."],
                "prettier.configPath": ".prettierrc"
            })
        
        return settings
    
    def create_project_structure(self, project_type: str, project_name: str) -> Dict[str, str]:
        """Create project structure files and directories."""
        
        structures = {
            "fastapi": {
                "main.py": "from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/')\nasync def root():\n    return {'message': 'Hello World'}",
                "requirements.txt": "fastapi==0.104.0\nuvicorn==0.24.0",
                ".gitignore": "__pycache__/\n*.pyc\nvenv/\n.env\n*.db",
                "README.md": f"# {project_name}\n\nFastAPI application"
            },
            "nextjs": {
                "package.json": f'{{"name": "{project_name}", "version": "0.1.0", "private": true}}',
                ".gitignore": "node_modules/\n.next/\n.env.local\n.env.development.local",
                "README.md": f"# {project_name}\n\nNext.js application"
            }
        }
        
        return structures.get(project_type, {})


# Singleton instance
coding_buddy = CodingBuddy()
