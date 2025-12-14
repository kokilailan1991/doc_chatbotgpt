"""
Workflow Processing Module
Handles all workflow types: Extract Insights, Action Items, Summaries, etc.
"""
import json
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import os


class WorkflowProcessor:
    def __init__(self, openai_key: str):
        self.llm = ChatOpenAI(temperature=0, openai_api_key=openai_key)
        self.output_parser = StrOutputParser()
    
    def _create_chain(self, template: str, retriever):
        """Create a LangChain chain for processing"""
        prompt = PromptTemplate.from_template(template)
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | self.output_parser
        )
        return chain
    
    def extract_insights(self, retriever, document_type: str = "general") -> Dict[str, Any]:
        """Extract key insights from document"""
        template = """Analyze the following document and extract key insights in JSON format.
        
Document Type: {document_type}
Context: {{context}}

Extract and return a JSON object with:
- keyEntities: [list of important entities, people, companies, dates]
- keyFindings: [list of important findings or facts]
- issues: [list of issues, errors, or concerns]
- opportunities: [list of opportunities or recommendations]
- risks: [list of potential risks]
- summary: brief overall summary

Return ONLY valid JSON, no additional text.
"""
        
        # Format document_type, then replace double braces with single for context
        formatted_template = template.format(document_type=document_type).replace("{{context}}", "{context}")
        chain = self._create_chain(formatted_template, retriever)
        result = chain.invoke("Extract insights")
        
        try:
            # Try to parse JSON from result
            if result.strip().startswith('{'):
                return json.loads(result)
            else:
                # Extract JSON if wrapped in text
                import re
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
        except:
            pass
        
        # Fallback: return structured text
        return {
            "keyEntities": [],
            "keyFindings": [],
            "issues": [],
            "opportunities": [],
            "risks": [],
            "summary": result
        }
    
    def generate_action_items(self, retriever) -> List[Dict[str, str]]:
        """Generate actionable items from document"""
        template = """Extract action items from the following document.
        
Context: {context}

Return a JSON array of action items, each with:
- title: action item title
- description: detailed description
- priority: "high", "medium", or "low"
- assignee: suggested assignee (if mentioned)
- dueDate: suggested due date (if mentioned)

Return ONLY valid JSON array, no additional text.
"""
        
        chain = self._create_chain(template, retriever)
        result = chain.invoke("Extract action items")
        
        try:
            if result.strip().startswith('['):
                return json.loads(result)
            import re
            json_match = re.search(r'\[.*\]', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return [{"title": "Review document", "description": result[:200], "priority": "medium"}]
    
    def create_summary(self, retriever, summary_type: str = "executive") -> str:
        """Create summary of document"""
        summary_types = {
            "executive": "Create an executive summary (2-3 paragraphs)",
            "detailed": "Create a detailed summary covering all major points",
            "bullet": "Create a bullet-point summary"
        }
        
        template = f"""{summary_types.get(summary_type, summary_types['executive'])} of the following document.
        
Context: {{context}}

Summary:"""
        
        chain = self._create_chain(template, retriever)
        return chain.invoke("Create summary")
    
    def generate_email_draft(self, retriever, email_type: str = "summary") -> Dict[str, str]:
        """Generate email draft based on document"""
        template = """Based on the following document, create an email draft.
        
Email Type: {email_type}
Context: {{context}}

Return a JSON object with:
- subject: email subject line
- body: email body (formatted)
- recipients: suggested recipients (if mentioned)

Return ONLY valid JSON, no additional text.
"""
        
        # Format email_type, then replace double braces with single for context
        formatted_template = template.format(email_type=email_type).replace("{{context}}", "{context}")
        chain = self._create_chain(formatted_template, retriever)
        result = chain.invoke("Generate email")
        
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
            "subject": "Document Summary",
            "body": result,
            "recipients": []
        }
    
    def produce_risk_analysis(self, retriever) -> Dict[str, Any]:
        """Produce risk analysis from document"""
        template = """Analyze the following document for risks and create a risk analysis.
        
Context: {context}

Return a JSON object with:
- risks: [array of risk objects with: title, description, severity (high/medium/low), mitigation]
- overallRiskLevel: "high", "medium", or "low"
- recommendations: [array of recommendations]

Return ONLY valid JSON, no additional text.
"""
        
        chain = self._create_chain(template, retriever)
        result = chain.invoke("Analyze risks")
        
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
            "risks": [],
            "overallRiskLevel": "medium",
            "recommendations": []
        }
    
    def compare_documents(self, retriever1, retriever2, comparison_type: str = "general") -> Dict[str, Any]:
        """Compare two documents"""
        # Get summaries of both documents first
        summary1 = self.create_summary(retriever1, "executive")
        summary2 = self.create_summary(retriever2, "executive")
        
        template = """Compare the following two documents and provide a comparison.
        
Document 1 Summary: {summary1}
Document 2 Summary: {summary2}

Return a JSON object with:
- similarities: [list of similarities]
- differences: [list of key differences]
- recommendations: [recommendations based on comparison]

Return ONLY valid JSON, no additional text.
"""
        
        # Use a simple chain for comparison
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm | self.output_parser
        
        result = chain.invoke({
            "summary1": summary1,
            "summary2": summary2
        })
        
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
            "similarities": [],
            "differences": [result],
            "recommendations": []
        }







