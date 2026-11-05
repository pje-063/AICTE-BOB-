"""
knowledge_base.py – Static interview knowledge base seeder.
Populates the ChromaDB vector store with curated role-specific interview questions,
HR guidelines, behavioural scenarios, and technical assessment material so that the
RAG pipeline has a rich retrieval corpus even before any user uploads a resume.
"""

INTERVIEW_KNOWLEDGE_BASE = [
    # ── Software Engineering ──────────────────────────────────────────────────
    {
        "id": "se_001",
        "role": "Software Engineer",
        "category": "technical",
        "level": "entry",
        "content": (
            "Common entry-level Software Engineer interview questions:\n"
            "1. Explain the difference between a stack and a queue with examples.\n"
            "2. What is Big-O notation? Give the complexity of common sorting algorithms.\n"
            "3. Describe the SOLID principles of object-oriented design.\n"
            "4. What is the difference between synchronous and asynchronous programming?\n"
            "5. Explain RESTful API design and HTTP methods (GET, POST, PUT, DELETE).\n"
            "Model answer tip: Use the STAR method for behavioural parts and provide "
            "concrete code examples for technical parts."
        ),
    },
    {
        "id": "se_002",
        "role": "Software Engineer",
        "category": "technical",
        "level": "senior",
        "content": (
            "Senior Software Engineer interview questions:\n"
            "1. Design a URL shortener system (system design).\n"
            "2. Describe microservices vs monolithic architecture trade-offs.\n"
            "3. How do you ensure high availability and fault tolerance in distributed systems?\n"
            "4. Explain CAP theorem with a real-world example.\n"
            "5. Walk through your approach to code review and technical debt management.\n"
            "Improvement tip: Quantify impact ('reduced latency by 40%') in every answer."
        ),
    },
    # ── Data Science / ML ─────────────────────────────────────────────────────
    {
        "id": "ds_001",
        "role": "Data Scientist",
        "category": "technical",
        "level": "mid",
        "content": (
            "Data Scientist interview questions (mid-level):\n"
            "1. Explain bias-variance trade-off.\n"
            "2. How do you handle class imbalance in a dataset?\n"
            "3. Compare Random Forest vs Gradient Boosting.\n"
            "4. What is regularisation and when would you apply L1 vs L2?\n"
            "5. Walk through a machine learning project lifecycle end-to-end.\n"
            "Preparation strategy: Revise statistics, practice on Kaggle datasets, "
            "and be ready to code a model from scratch in Python."
        ),
    },
    # ── Product Manager ───────────────────────────────────────────────────────
    {
        "id": "pm_001",
        "role": "Product Manager",
        "category": "behavioral",
        "level": "mid",
        "content": (
            "Product Manager behavioural interview questions:\n"
            "1. Tell me about a product you improved significantly. What metrics moved?\n"
            "2. How do you prioritise features when resources are limited?\n"
            "3. Describe a time you disagreed with engineering on a technical decision.\n"
            "4. How do you gather and validate customer requirements?\n"
            "5. Walk me through how you'd define success for a new feature.\n"
            "Tip: Use the CIRCLES method for product design questions and STAR for "
            "behavioural questions."
        ),
    },
    # ── DevOps / Cloud ────────────────────────────────────────────────────────
    {
        "id": "devops_001",
        "role": "DevOps Engineer",
        "category": "technical",
        "level": "mid",
        "content": (
            "DevOps Engineer interview questions:\n"
            "1. Explain CI/CD pipeline stages and tools you've used.\n"
            "2. What is Infrastructure as Code? Compare Terraform vs Ansible.\n"
            "3. How do you monitor microservices in production?\n"
            "4. Describe Kubernetes pod scheduling and resource management.\n"
            "5. What is a blue-green deployment and when would you use it?\n"
            "Preparation tip: Demonstrate hands-on experience with Docker, Kubernetes, "
            "Jenkins/GitLab CI, and cloud platforms (AWS/GCP/IBM Cloud)."
        ),
    },
    # ── HR / Behavioural Universal ─────────────────────────────────────────────
    {
        "id": "hr_001",
        "role": "all",
        "category": "hr",
        "level": "all",
        "content": (
            "Universal HR interview questions and model answers:\n"
            "1. Tell me about yourself.\n"
            "   Model: 2-minute structured pitch: current role → key achievements → "
            "why this company.\n"
            "2. What is your greatest weakness?\n"
            "   Model: Choose a real weakness, show self-awareness, explain the steps "
            "you're taking to improve.\n"
            "3. Where do you see yourself in 5 years?\n"
            "   Model: Align growth goals with the company's direction.\n"
            "4. Why do you want to leave your current job?\n"
            "   Model: Keep positive; focus on growth opportunities ahead, not problems behind.\n"
            "5. What are your salary expectations?\n"
            "   Model: Research market rates, give a range, and express flexibility."
        ),
    },
    {
        "id": "hr_002",
        "role": "all",
        "category": "behavioral",
        "level": "all",
        "content": (
            "STAR Method guide for behavioural interview answers:\n"
            "Situation – Set the context in 1-2 sentences.\n"
            "Task – Describe your responsibility.\n"
            "Action – Detail the specific steps YOU took (use 'I', not 'we').\n"
            "Result – Quantify the outcome wherever possible.\n\n"
            "Common behavioural questions:\n"
            "- Describe a conflict with a teammate and how you resolved it.\n"
            "- Give an example of a time you failed and what you learned.\n"
            "- Tell me about a time you had to deliver under a tight deadline.\n"
            "- Describe a situation where you led without formal authority.\n"
            "- Give an example of a creative solution you proposed."
        ),
    },
    # ── Frontend Developer ────────────────────────────────────────────────────
    {
        "id": "fe_001",
        "role": "Frontend Developer",
        "category": "technical",
        "level": "mid",
        "content": (
            "Frontend Developer interview questions:\n"
            "1. Explain the Virtual DOM in React and why it improves performance.\n"
            "2. What is CSS specificity and how is it calculated?\n"
            "3. Describe the browser rendering pipeline (parse, style, layout, paint, composite).\n"
            "4. How do you optimise a web application's load time?\n"
            "5. Explain event bubbling and event delegation.\n"
            "Preparation strategy: Build a portfolio project, review browser DevTools "
            "profiling, and practice JavaScript fundamentals."
        ),
    },
    # ── Backend Developer ─────────────────────────────────────────────────────
    {
        "id": "be_001",
        "role": "Backend Developer",
        "category": "technical",
        "level": "mid",
        "content": (
            "Backend Developer interview questions:\n"
            "1. Explain database indexing and when NOT to use an index.\n"
            "2. What is the N+1 query problem and how do you fix it?\n"
            "3. Describe OAuth 2.0 authentication flow.\n"
            "4. How would you design a rate-limiting mechanism for an API?\n"
            "5. Compare SQL and NoSQL databases with use-case examples.\n"
            "Tip: Be ready to write raw SQL queries and discuss transaction isolation levels."
        ),
    },
    # ── Industry expectations ─────────────────────────────────────────────────
    {
        "id": "industry_001",
        "role": "all",
        "category": "industry",
        "level": "all",
        "content": (
            "2024-2025 Hiring industry expectations:\n"
            "- Companies value AI/ML literacy across all technical roles.\n"
            "- Cloud-native experience (AWS, GCP, Azure, IBM Cloud) is highly preferred.\n"
            "- Communication and cross-functional collaboration are rated as critical.\n"
            "- Coding assessments typically include LeetCode medium-level problems.\n"
            "- System design rounds are standard from senior level onwards.\n"
            "- Diversity, equity, and inclusion values are assessed in cultural-fit rounds.\n"
            "- Open-source contributions and side projects significantly strengthen profiles."
        ),
    },
    # ── Improvement Tips ──────────────────────────────────────────────────────
    {
        "id": "tips_001",
        "role": "all",
        "category": "improvement",
        "level": "all",
        "content": (
            "Interview preparation improvement tips:\n"
            "1. Mock Interviews: Practice with a friend or record yourself; review filler words.\n"
            "2. Company Research: Study the company's products, culture, and recent news.\n"
            "3. Question List: Prepare 5 thoughtful questions to ask the interviewer.\n"
            "4. Technical Practice: Solve 2 coding problems daily for 4 weeks before the interview.\n"
            "5. Body Language: Maintain eye contact, sit upright, avoid crossing arms.\n"
            "6. Follow-Up: Send a thank-you email within 24 hours of the interview.\n"
            "7. Storytelling: Each answer should tell a brief, impactful story."
        ),
    },
]
