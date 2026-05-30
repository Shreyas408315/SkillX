ROLE_SKILLS: dict[str, dict[str, list[str]]] = {
    "frontend developer": {
        "required": ["html", "css", "javascript", "react", "typescript", "git"],
        "optional": ["next.js", "redux", "testing", "figma", "accessibility", "responsive design", "tailwind css"],
    },
    "backend developer": {
        "required": ["python", "node.js", "sql", "rest api", "docker", "git"],
        "optional": ["postgresql", "mongodb", "aws", "django", "flask", "system design", "microservices", "redis", "express"],
    },
    "full stack developer": {
        "required": ["javascript", "react", "node.js", "sql", "git", "docker"],
        "optional": ["typescript", "mongodb", "postgresql", "aws", "testing", "express", "rest api", "html", "css"],
    },
    "data scientist": {
        "required": ["python", "sql", "machine learning", "pandas", "numpy", "statistics"],
        "optional": ["tensorflow", "pytorch", "tableau", "nlp", "data visualization", "scikit-learn", "deep learning"],
    },
    "machine learning engineer": {
        "required": ["python", "machine learning", "tensorflow", "pytorch", "sql", "docker"],
        "optional": ["aws", "nlp", "mlops", "data engineering", "kubernetes", "deep learning", "scikit-learn"],
    },
    "devops engineer": {
        "required": ["docker", "aws", "kubernetes", "linux", "ci/cd", "git"],
        "optional": ["terraform", "monitoring", "python", "networking", "jenkins", "ansible", "cloudformation"],
    },
    "software engineer": {
        "required": ["python", "git", "system design", "rest api", "docker", "sql"],
        "optional": ["aws", "microservices", "testing", "kubernetes", "linux", "react"],
    },
}


SKILL_ALIASES = {
    "nodejs": "node.js",
    "node js": "node.js",
    "express.js": "express",
    "restful api": "rest api",
    "rest apis": "rest api",
    "ci cd": "ci/cd",
    "machine-learning": "machine learning",
    "nlp engineer": "nlp",
    "amazon web services": "aws",
    "apis": "rest api",
    "postgres": "postgresql",
    "mongo": "mongodb",
    "tailwind": "tailwind css",
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "ci/cd pipelines": "ci/cd",
    "micro services": "microservices",
    "k8s": "kubernetes",
    "site reliability engineer": "devops engineer",
    "sre": "devops engineer",
    "software engineer": "software engineer",
    "software developer": "software engineer",
}


ROLE_ALIASES = {
    "frontend": "frontend developer",
    "frontend engineer": "frontend developer",
    "react developer": "frontend developer",
    "backend": "backend developer",
    "backend engineer": "backend developer",
    "python developer": "backend developer",
    "node.js developer": "backend developer",
    "fullstack developer": "full stack developer",
    "fullstack engineer": "full stack developer",
    "software engineer": "software engineer",
    "software developer": "software engineer",
    "data scientist": "data scientist",
    "ml engineer": "machine learning engineer",
    "machine learning engineer": "machine learning engineer",
    "devops": "devops engineer",
    "devops engineer": "devops engineer",
    "site reliability engineer": "devops engineer",
}
