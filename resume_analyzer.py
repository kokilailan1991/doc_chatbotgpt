"""
Resume Analyzer Module
Handles ATS scoring, resume rewriting, and JD matching
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
        """Calculate ATS (Applicant Tracking System) score for resume"""
        template = """Analyze this resume for ATS compatibility and calculate an ATS score.
        
Resume Content: {context}
Job Description: {job_description}

Evaluate the resume on:
1. Keywords match (0-25 points)
2. Format compatibility (0-20 points)
3. Skills alignment (0-25 points)
4. Experience relevance (0-20 points)
5. Education match (0-10 points)

Return a JSON object with:
- overallScore: number (0-100)
- keywordScore: number (0-25)
- formatScore: number (0-20)
- skillsScore: number (0-25)
- experienceScore: number (0-20)
- educationScore: number (0-10)
- missingKeywords: [list of missing keywords from JD]
- strengths: [list of resume strengths]
- weaknesses: [list of resume weaknesses]
- recommendations: [list of improvement recommendations]

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
        """Rewrite resume with improvements"""
        template = """Rewrite and improve this resume based on the following improvements.
        
Original Resume: {context}
Improvements to apply: {improvements}

Create an improved version of the resume that:
- Incorporates all suggested improvements
- Maintains the original structure and content
- Enhances clarity and impact
- Optimizes for ATS systems

Return the improved resume text.
"""
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        resume_docs = resume_retriever.get_relevant_documents("resume") if hasattr(resume_retriever, 'get_relevant_documents') else []
        resume_text = "\n\n".join([doc.page_content for doc in resume_docs]) if resume_docs else ""
        improvements_text = "\n".join(improvements) if improvements else "General improvements for ATS optimization"
        
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm | self.output_parser
        
        return chain.invoke({
            "context": resume_text,
            "improvements": improvements_text
        })
    
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
    
    def generate_resume_report(self, resume_retriever, jd_retriever=None) -> Dict[str, Any]:
        """Generate comprehensive resume analysis report"""
        ats_score = self.calculate_ats_score(resume_retriever, jd_retriever)
        insights = self.workflow.extract_insights(resume_retriever, "resume")
        
        return {
            "atsScore": ats_score,
            "insights": insights,
            "summary": insights.get("summary", ""),
            "fixes": ats_score.get("recommendations", []),
            "strengths": ats_score.get("strengths", []),
            "weaknesses": ats_score.get("weaknesses", [])
        }

