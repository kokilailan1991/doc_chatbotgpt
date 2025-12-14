"""
Resume Analyzer Module - Enhanced Viral Version
Handles ATS scoring, grammar fixes, skill gaps, keyword optimization, JD matching, and resume rewriting
"""
import json
from typing import Dict, List, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from workflows import WorkflowProcessor


class ResumeAnalyzer:
    def __init__(self, openai_key: str):
        self.llm = ChatOpenAI(temperature=0, openai_api_key=openai_key)
        self.output_parser = StrOutputParser()
        self.workflow = WorkflowProcessor(openai_key)
    
    def calculate_ats_score(self, resume_retriever, jd_retriever=None) -> Dict[str, Any]:
        """Calculate ATS (Applicant Tracking System) score for resume - detailed analysis"""
        template = """Analyze this resume comprehensively for ATS compatibility and calculate a detailed ATS score.

Resume Content: {context}
Job Description: {job_description}

Evaluate the resume on these criteria with specific, detailed feedback:

1. Keywords match (0-25 points): Check if resume contains relevant keywords from job description. List specific missing keywords.
2. Format compatibility (0-20 points): Assess if resume uses ATS-friendly format (standard fonts, clear sections, no graphics/tables that break parsing).
3. Skills alignment (0-25 points): Compare resume skills with job requirements. Identify matching and missing skills.
4. Experience relevance (0-20 points): Evaluate how well work experience matches job requirements. Assess years of experience, industry relevance.
5. Education match (0-10 points): Check if education meets job requirements.

Return a JSON object with:
- overallScore: number (0-100)
- keywordScore: number (0-25)
- formatScore: number (0-20)
- skillsScore: number (0-25)
- experienceScore: number (0-20)
- educationScore: number (0-10)
- missingKeywords: [array of specific missing keywords from JD, e.g., "Python", "Project Management", "Agile"]
- strengths: [array of specific strengths with details, e.g., "Strong technical skills section with relevant programming languages", "Clear work history with quantifiable achievements", "ATS-friendly format with standard sections"]
- weaknesses: [array of specific weaknesses with details, e.g., "Missing key skill: 'Machine Learning' mentioned in job description", "Work experience descriptions lack quantifiable metrics", "Resume format may not be fully ATS-compatible due to complex formatting"]
- recommendations: [array of specific, actionable recommendations, e.g., "Add 'Python' and 'SQL' to skills section as they are required in job description", "Quantify achievements in experience section (e.g., 'Increased sales by 25%' instead of 'Improved sales')", "Simplify resume format - remove tables and graphics that may confuse ATS systems"]

IMPORTANT: Provide specific, detailed feedback. Avoid generic statements like "good format" or "needs improvement". Be specific about what is good and what needs to be changed.

Return ONLY valid JSON, no additional text.
"""
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        resume_docs = resume_retriever.get_relevant_documents("resume") if hasattr(resume_retriever, 'get_relevant_documents') else []
        resume_text = "\n\n".join([doc.page_content for doc in resume_docs]) if resume_docs else ""
        
        jd_text = ""
        if jd_retriever:
            jd_docs = jd_retriever.get_relevant_documents("job description") if hasattr(jd_retriever, 'get_relevant_documents') else []
            jd_text = "\n\n".join([doc.page_content for doc in jd_docs]) if jd_docs else ""
        
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm | self.output_parser
        
        result = chain.invoke({
            "context": resume_text,
            "job_description": jd_text or "General resume evaluation"
        })
        
        try:
            if result.strip().startswith('{'):
                return json.loads(result)
            import re
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            print(f"Error parsing ATS score: {e}")
        
        # Fallback
        return {
            "overallScore": 70,
            "keywordScore": 15,
            "formatScore": 15,
            "skillsScore": 15,
            "experienceScore": 15,
            "educationScore": 10,
            "missingKeywords": [],
            "strengths": ["Well formatted"],
            "weaknesses": ["Could improve keyword optimization"],
            "recommendations": ["Add more relevant keywords"]
        }
    
    def rewrite_resume(self, resume_retriever, improvements: List[str] = None) -> str:
        """Rewrite resume with improvements - comprehensive and accurate"""
        template = """You are an expert resume writer. Rewrite and improve this resume based on the following improvements.

Original Resume Content:
{context}

Improvements to Apply:
{improvements}

IMPORTANT INSTRUCTIONS:
1. Maintain the EXACT structure and sections from the original resume (e.g., if it has "Experience", "Education", "Skills", keep those sections)
2. Keep ALL factual information accurate (names, dates, companies, job titles, degrees, etc.)
3. Enhance bullet points with action verbs and quantifiable achievements
4. Optimize keywords for ATS systems while keeping content natural
5. Improve clarity and impact of descriptions
6. Fix any grammar or formatting issues
7. Make the resume more compelling and professional
8. DO NOT create fake or placeholder content - only improve what exists

Return the COMPLETE improved resume in a clear, well-formatted structure. Include all sections from the original resume with improvements applied.
"""
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        resume_docs = resume_retriever.get_relevant_documents("resume") if hasattr(resume_retriever, 'get_relevant_documents') else []
        if not resume_docs:
            resume_docs = resume_retriever.get_relevant_documents("document") if hasattr(resume_retriever, 'get_relevant_documents') else []
        
        resume_text = "\n\n".join([doc.page_content for doc in resume_docs]) if resume_docs else ""
        
        if not resume_text or len(resume_text.strip()) < 50:
            return "Error: Could not extract resume content. Please ensure the resume PDF is readable."
        
        improvements_text = "\n".join(improvements) if improvements else "General improvements: Optimize for ATS, enhance clarity, use action verbs, add quantifiable achievements"
        
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm | self.output_parser
        
        try:
            result = chain.invoke({
                "context": resume_text[:10000],  # Limit context for better performance
                "improvements": improvements_text
            })
            
            # Validate that we got actual content, not placeholder
            if result and len(result.strip()) > 100 and not any(placeholder in result.lower() for placeholder in ['lorem', 'ipsum', 'placeholder', 'example text']):
                return result
            else:
                return "Error: Generated resume appears to be incomplete. Please try again."
        except Exception as e:
            return f"Error generating rewritten resume: {str(e)}"
    
    def match_with_jd(self, resume_retriever, jd_retriever) -> Dict[str, Any]:
        """Match resume with job description"""
        ats_score = self.calculate_ats_score(resume_retriever, jd_retriever)
        
        template = """Analyze how well this resume matches the job description.
        
Resume: {resume}
Job Description: {job_description}

Provide a detailed matching analysis including:
- Key matches (skills, experience, qualifications)
- Gaps and missing requirements
- Suggestions for improvement
- Overall fit assessment

Return a JSON object with:
- matchPercentage: number (0-100)
- keyMatches: [list of matching points]
- gaps: [list of gaps or missing requirements]
- suggestions: [list of improvement suggestions]
- fitAssessment: "excellent", "good", "fair", or "poor"

Return ONLY valid JSON, no additional text.
"""
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        resume_docs = resume_retriever.get_relevant_documents("resume") if hasattr(resume_retriever, 'get_relevant_documents') else []
        resume_text = "\n\n".join([doc.page_content for doc in resume_docs]) if resume_docs else ""
        jd_docs = jd_retriever.get_relevant_documents("job description") if hasattr(jd_retriever, 'get_relevant_documents') else []
        jd_text = "\n\n".join([doc.page_content for doc in jd_docs]) if jd_docs else ""
        
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm | self.output_parser
        
        result = chain.invoke({
            "resume": resume_text,
            "job_description": jd_text
        })
        
        try:
            if result.strip().startswith('{'):
                match_data = json.loads(result)
            else:
                import re
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    match_data = json.loads(json_match.group())
                else:
                    match_data = {}
        except:
            match_data = {}
        
        # Combine ATS score with match analysis
        return {
            "atsScore": ats_score,
            "matchPercentage": match_data.get("matchPercentage", ats_score.get("overallScore", 70)),
            "keyMatches": match_data.get("keyMatches", []),
            "gaps": match_data.get("gaps", ats_score.get("missingKeywords", [])),
            "suggestions": match_data.get("suggestions", ats_score.get("recommendations", [])),
            "fitAssessment": match_data.get("fitAssessment", "good")
        }
    
    def analyze_grammar_clarity(self, resume_retriever) -> Dict[str, Any]:
        """Analyze grammar and clarity issues"""
        template = """Analyze this resume for grammar, clarity, and writing quality issues.
        
Resume: {context}

Return a JSON object with:
- grammarErrors: [list of grammar errors with corrections]
- clarityIssues: [list of unclear phrases with suggestions]
- bulletPointImprovements: [list of bullet points with improved versions]
- overallWritingScore: number (0-100)
- recommendations: [list of writing improvement recommendations]

Return ONLY valid JSON, no additional text.
"""
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        resume_docs = resume_retriever.get_relevant_documents("resume") if hasattr(resume_retriever, 'get_relevant_documents') else []
        resume_text = "\n\n".join([doc.page_content for doc in resume_docs]) if resume_docs else ""
        
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm | self.output_parser
        
        result = chain.invoke({"context": resume_text})
        
        try:
            if result.strip().startswith('{'):
                return json.loads(result)
            import re
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "grammarErrors": [],
            "clarityIssues": [],
            "bulletPointImprovements": [],
            "overallWritingScore": 75,
            "recommendations": []
        }
    
    def analyze_skill_gaps(self, resume_retriever, jd_retriever) -> Dict[str, Any]:
        """Analyze skill gaps between resume and JD"""
        template = """Compare the skills in this resume with the job description requirements.
        
Resume: {resume}
Job Description: {jd}

Return a JSON object with:
- matchingSkills: [list of skills that match]
- missingSkills: [list of required skills missing from resume]
- skillGapScore: number (0-100)
- recommendations: [list of skills to add]

Return ONLY valid JSON, no additional text.
"""
        
        resume_docs = resume_retriever.get_relevant_documents("resume") if hasattr(resume_retriever, 'get_relevant_documents') else []
        resume_text = "\n\n".join([doc.page_content for doc in resume_docs]) if resume_docs else ""
        jd_docs = jd_retriever.get_relevant_documents("job description") if hasattr(jd_retriever, 'get_relevant_documents') else []
        jd_text = "\n\n".join([doc.page_content for doc in jd_docs]) if jd_docs else ""
        
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm | self.output_parser
        
        result = chain.invoke({"resume": resume_text, "jd": jd_text})
        
        try:
            if result.strip().startswith('{'):
                return json.loads(result)
            import re
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "matchingSkills": [],
            "missingSkills": [],
            "skillGapScore": 70,
            "recommendations": []
        }
    
    def optimize_keywords(self, resume_retriever, jd_retriever=None) -> Dict[str, Any]:
        """Optimize resume keywords for ATS"""
        template = """Analyze this resume for keyword optimization opportunities.
        
Resume: {resume}
Job Description: {jd}

Return a JSON object with:
- currentKeywords: [list of keywords found in resume]
- recommendedKeywords: [list of keywords to add]
- keywordDensity: number (0-100)
- optimizationSuggestions: [list of specific suggestions]

Return ONLY valid JSON, no additional text.
"""
        
        resume_docs = resume_retriever.get_relevant_documents("resume") if hasattr(resume_retriever, 'get_relevant_documents') else []
        resume_text = "\n\n".join([doc.page_content for doc in resume_docs]) if resume_docs else ""
        jd_text = ""
        if jd_retriever:
            jd_docs = jd_retriever.get_relevant_documents("job description") if hasattr(jd_retriever, 'get_relevant_documents') else []
            jd_text = "\n\n".join([doc.page_content for doc in jd_docs]) if jd_docs else ""
        
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm | self.output_parser
        
        result = chain.invoke({"resume": resume_text, "jd": jd_text or "General resume optimization"})
        
        try:
            if result.strip().startswith('{'):
                return json.loads(result)
            import re
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "currentKeywords": [],
            "recommendedKeywords": [],
            "keywordDensity": 60,
            "optimizationSuggestions": []
        }
    
    def generate_resume_report(self, resume_retriever, jd_retriever=None) -> Dict[str, Any]:
        """Generate comprehensive resume analysis report with all enhancements"""
        ats_score = self.calculate_ats_score(resume_retriever, jd_retriever)
        insights = self.workflow.extract_insights(resume_retriever, "resume")
        grammar_analysis = self.analyze_grammar_clarity(resume_retriever)
        keyword_optimization = self.optimize_keywords(resume_retriever, jd_retriever)
        
        skill_gaps = {}
        if jd_retriever:
            skill_gaps = self.analyze_skill_gaps(resume_retriever, jd_retriever)
        
        # Generate rewritten resume
        improvements = (
            ats_score.get("recommendations", []) +
            grammar_analysis.get("recommendations", []) +
            keyword_optimization.get("optimizationSuggestions", [])
        )
        rewritten_resume = self.rewrite_resume(resume_retriever, improvements)
        
        return {
            "atsScore": ats_score,
            "insights": insights,
            "grammarAnalysis": grammar_analysis,
            "keywordOptimization": keyword_optimization,
            "skillGaps": skill_gaps,
            "summary": insights.get("summary", ""),
            "fixes": ats_score.get("recommendations", []),
            "strengths": ats_score.get("strengths", []),
            "weaknesses": ats_score.get("weaknesses", []),
            "rewrittenResume": rewritten_resume,
            "cards": {
                "card1": {
                    "title": "ATS Score",
                    "score": ats_score.get("overallScore", 0),
                    "summary": insights.get("summary", "")
                },
                "card2": {
                    "title": "Strengths",
                    "items": ats_score.get("strengths", [])
                },
                "card3": {
                    "title": "Weaknesses",
                    "items": ats_score.get("weaknesses", [])
                },
                "card4": {
                    "title": "JD Match",
                    "matchScore": skill_gaps.get("skillGapScore", 0) if skill_gaps else None,
                    "matchingSkills": skill_gaps.get("matchingSkills", []) if skill_gaps else [],
                    "missingSkills": skill_gaps.get("missingSkills", []) if skill_gaps else []
                },
                "card5": {
                    "title": "Rewritten Resume",
                    "content": rewritten_resume
                }
            }
        }

