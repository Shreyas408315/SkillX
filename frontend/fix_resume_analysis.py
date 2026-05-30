import re

file_path = "resume-analysis.html"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# We want to replace everything from `        // Category keyword maps for scoring`
# up to `        function renderResults(results) {`

start_marker = "        // Category keyword maps for scoring"
end_marker = "        function renderResults(results) {"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print("Markers not found!")
    exit(1)

new_code = """        // Category keyword maps for scoring
        const categoryKeywords = {
            'Technical Skills': ['javascript', 'python', 'java', 'c++', 'react', 'angular', 'vue', 'node', 'express', 'django', 'flask', 'sql', 'nosql', 'mongodb', 'postgresql', 'mysql', 'html', 'css', 'typescript', 'rust', 'go', 'kotlin', 'swift', 'php', 'ruby', 'r', 'matlab', 'scala', 'graphql', 'rest', 'api'],
            'Cloud & DevOps': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'ci/cd', 'jenkins', 'terraform', 'ansible', 'linux', 'nginx', 'serverless', 'lambda', 'cloudformation', 'microservices', 'devops', 'git', 'github', 'gitlab', 'bitbucket'],
            'Data & AI/ML': ['machine learning', 'deep learning', 'tensorflow', 'pytorch', 'nlp', 'computer vision', 'data science', 'data analysis', 'pandas', 'numpy', 'scikit', 'hadoop', 'spark', 'tableau', 'power bi', 'statistics', 'neural network', 'ai', 'artificial intelligence', 'big data'],
            'Soft Skills': ['leadership', 'communication', 'teamwork', 'problem solving', 'analytical', 'management', 'presentation', 'collaboration', 'mentoring', 'agile', 'scrum', 'project management', 'critical thinking', 'creative', 'negotiation', 'strategic'],
            'Education': ['bachelor', 'master', 'phd', 'b.tech', 'b.sc', 'bca', 'mca', 'mba', 'bba', 'm.tech', 'degree', 'university', 'college', 'institute', 'certification', 'certified', 'diploma', 'coursework', 'gpa', 'cgpa'],
            'Experience': ['years', 'experience', 'internship', 'intern', 'worked', 'developed', 'built', 'designed', 'implemented', 'managed', 'led', 'contributed', 'deployed', 'maintained', 'created', 'launched', 'optimized', 'achieved', 'increased', 'reduced']
        };

        async function analyzeResume() {
            const resumeText = document.getElementById('resumeText').value.trim();
            const jobDesc = document.getElementById('jobDescription').value.trim();

            if (!resumeText) {
                alert('Please paste your resume text first!');
                return;
            }

            const btn = document.getElementById('analyzeBtn');
            btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Analyzing...';
            btn.disabled = true;

            try {
                const parsed = await SkillXApi.post('/resume/parse', {
                    resume_text: resumeText
                });
                const match = jobDesc ? await SkillXApi.post('/match/score', {
                    resume_text: resumeText,
                    job_description: jobDesc
                }) : null;
                const results = buildAnalysisResults(resumeText, parsed, match);
                renderResults(results);
            } catch (error) {
                alert(`Analysis failed: ${error.message}`);
            } finally {
                btn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Re-Analyze';
                btn.disabled = false;
            }
        }

        function buildAnalysisResults(resume, parsed, match) {
            const resumeLower = resume.toLowerCase();
            const wordCount = resume.split(/\\s+/).filter(w => w.length > 0).length;
            const lineCount = resume.split(/\\n/).filter(l => l.trim().length > 0).length;
            const sentenceCount = resume.split(/[.!?]+/).filter(s => s.trim().length > 0).length;

            const categoryScores = computeCategoryScores(resumeLower, parsed.skills || []);
            const catVals = Object.values(categoryScores);
            const overallScore = match ? match.match_score : Math.round(catVals.reduce((a, b) => a + b, 0) / catVals.length);
            const matchedKeywords = match?.matched_skills || [];
            const missingKeywords = match?.missing_skills || [];
            const totalKeywords = matchedKeywords.length + missingKeywords.length;
            const keywordMatchPercent = totalKeywords > 0 ? Math.round((matchedKeywords.length / totalKeywords) * 100) : null;
            const suggestions = generateSuggestions(categoryScores, wordCount, keywordMatchPercent, missingKeywords, match?.recommendations || [], parsed);

            return {
                wordCount,
                lineCount,
                sentenceCount,
                categoryScores,
                overallScore,
                matchedKeywords,
                missingKeywords,
                keywordMatchPercent,
                suggestions
            };
        }

        function computeCategoryScores(resumeLower, extractedSkills) {
            const skillSet = new Set((extractedSkills || []).map(skill => skill.toLowerCase()));
            const categoryScores = {};
            
            // Define realistic targets for how many keywords constitute a "100%" score in each category
            const categoryTargets = {
                'Technical Skills': 7,
                'Cloud & DevOps': 5,
                'Data & AI/ML': 4,
                'Soft Skills': 5,
                'Education': 2,
                'Experience': 6
            };

            for (const [category, keywords] of Object.entries(categoryKeywords)) {
                let found = 0;
                keywords.forEach(kw => {
                    if (resumeLower.includes(kw) || skillSet.has(kw)) found++;
                });
                
                const target = categoryTargets[category] || 5;
                categoryScores[category] = Math.min(100, Math.round((found / target) * 100));
            }
            return categoryScores;
        }

        function generateSuggestions(catScores, wordCount, kwMatch, missingKws, apiRecommendations, parsed) {
            const suggestions = [];

            if (wordCount < 150) suggestions.push('Your resume is quite short. Aim for at least 300-600 words to provide enough detail.');
            if (wordCount > 1000) suggestions.push('Your resume is very long. Consider trimming it to 1-2 pages for better recruiter engagement.');

            if (catScores['Technical Skills'] < 30) suggestions.push('Add more technical skills and tools relevant to your field (programming languages, frameworks, etc.).');
            if (catScores['Cloud & DevOps'] < 20) suggestions.push('Consider highlighting cloud platforms (AWS, Azure, GCP) or DevOps tools if applicable to your role.');
            if (catScores['Data & AI/ML'] < 15) suggestions.push('If data/AI is relevant to your career, mention tools like pandas, TensorFlow, or data analysis experience.');
            if (catScores['Soft Skills'] < 20) suggestions.push('Include soft skills like leadership, communication, and teamwork. Recruiters value these highly.');
            if (catScores['Education'] < 25) suggestions.push('Make sure your education section clearly lists your degrees, certifications, and institutions.');
            if (catScores['Experience'] < 30) suggestions.push('Use strong action verbs (developed, implemented, led, optimized) to describe your experience.');

            if (kwMatch !== null && kwMatch < 50) suggestions.push(`Only ${kwMatch}% of job description keywords were found. Tailor your resume to match the role.`);
            if (missingKws.length > 0) suggestions.push(`Consider adding these missing keywords: ${missingKws.slice(0, 6).join(', ')}.`);
            if ((parsed.skills || []) && (parsed.skills || []).length > 0 && (parsed.skills || []).length < 6) suggestions.push('Your resume exposes only a small skills footprint. Add more tools, frameworks, and technologies you have used.');
            if (parsed.projects && parsed.projects.length === 0) suggestions.push('Add at least one project with technologies and impact to strengthen your profile.');
            (apiRecommendations || []).forEach(item => suggestions.push(item.detail));

            if (suggestions.length === 0) suggestions.push('Your resume looks solid! Keep refining with real job descriptions for best results.');

            return [...new Set(suggestions)];
        }

"""

new_content = content[:start_idx] + new_code + content[end_idx:]

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)
print("File successfully restored and updated.")
