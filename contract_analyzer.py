"""
Professional Contract Analyzer Module
Analyzes contracts for legal compliance, risks, obligations, and missing clauses.
"""

import json
import re
from typing import Dict, Any, List
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough


class ContractAnalyzer:
    """Professional contract analysis system"""
    
    def __init__(self, openai_api_key: str):
        from langchain_openai import ChatOpenAI
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, openai_api_key=openai_api_key)
        self.output_parser = StrOutputParser()
    
    def _create_chain(self, template: str, retriever):
        """Create LangChain chain for document analysis"""
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        def get_context(query):
            docs = retriever.get_relevant_documents(query) if hasattr(retriever, 'get_relevant_documents') else []
            return format_docs(docs) if docs else ""
        
        prompt = PromptTemplate.from_template(template)
        chain = (
            {"context": RunnablePassthrough() | get_context}
            | prompt
            | self.llm
            | self.output_parser
        )
        return chain
    
    def analyze_contract(self, retriever) -> Dict[str, Any]:
        """Comprehensive contract analysis"""
        
        # Extract metadata
        metadata = self._extract_metadata(retriever)
        
        # Get summary
        summary = self._get_summary(retriever)
        
        # Extract obligations
        obligations = self._extract_obligations(retriever)
        
        # Analyze risks
        risks = self._analyze_risks(retriever)
        
        # Check for missing clauses
        missing_clauses = self._check_missing_clauses(retriever)
        
        # Identify key clauses
        key_clauses = self._identify_key_clauses(retriever)
        
        # Suggest improvements
        improvements = self._suggest_improvements(retriever, risks, missing_clauses)
        
        return {
            "summary": summary,
            "metadata": metadata,
            "providerObligations": obligations.get("provider", []),
            "clientObligations": obligations.get("client", []),
            "risks": risks,
            "missingClauses": missing_clauses,
            "keyClauses": key_clauses,
            "improvements": improvements,
            "overallRiskLevel": self._calculate_overall_risk(risks)
        }
    
    def _extract_metadata(self, retriever) -> Dict[str, Any]:
        """Extract contract metadata: parties, dates, value, etc."""
        template = """Extract key metadata from this contract document.

Context: {context}

Return a JSON object with:
- parties: {provider: "name", client: "name"}
- contractDate: "YYYY-MM-DD" or null
- effectiveDate: "YYYY-MM-DD" or null
- expirationDate: "YYYY-MM-DD" or null
- contractValue: "amount and currency" or null
- contractType: "Service Agreement", "Employment Contract", "NDA", etc.
- governingLaw: "jurisdiction" or null
- disputeResolution: "method" or null

Return ONLY valid JSON, no additional text.
"""
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        docs = retriever.get_relevant_documents("contract parties dates value") if hasattr(retriever, 'get_relevant_documents') else []
        content = format_docs(docs) if docs else ""
        
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm | self.output_parser
        
        result = chain.invoke({"context": content[:5000]})
        
        try:
            if result.strip().startswith('{'):
                return json.loads(result)
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {
            "parties": {"provider": "Unknown", "client": "Unknown"},
            "contractDate": None,
            "effectiveDate": None,
            "expirationDate": None,
            "contractValue": None,
            "contractType": "Contract",
            "governingLaw": None,
            "disputeResolution": None
        }
    
    def _get_summary(self, retriever) -> str:
        """Get executive summary of contract"""
        template = """Create a comprehensive executive summary of this contract (3-4 paragraphs).

Context: {context}

Summary should cover:
- Parties involved
- Main purpose and scope
- Key terms (payment, duration, deliverables)
- Important obligations
- Risk factors

Summary:"""
        
        chain = self._create_chain(template, retriever)
        return chain.invoke("Summarize contract")
    
    def _extract_obligations(self, retriever) -> Dict[str, List[Dict[str, str]]]:
        """Extract obligations for both parties"""
        template = """Extract all obligations for both parties from this contract.

Context: {context}

Return a JSON object with:
- provider: [array of obligations for provider/service provider]
- client: [array of obligations for client/customer]

Each obligation should be an object with:
- title: brief title
- description: detailed description
- deadline: deadline or timeframe if mentioned

Return ONLY valid JSON, no additional text.
"""
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        docs = retriever.get_relevant_documents("obligations responsibilities duties") if hasattr(retriever, 'get_relevant_documents') else []
        content = format_docs(docs) if docs else ""
        
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm | self.output_parser
        
        result = chain.invoke({"context": content[:5000]})
        
        try:
            if result.strip().startswith('{'):
                data = json.loads(result)
                return {
                    "provider": data.get("provider", []),
                    "client": data.get("client", [])
                }
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return {
                    "provider": data.get("provider", []),
                    "client": data.get("client", [])
                }
        except:
            pass
        
        return {"provider": [], "client": []}
    
    def _analyze_risks(self, retriever) -> List[Dict[str, str]]:
        """Analyze contract risks with severity levels"""
        template = """Analyze this contract for legal, financial, and operational risks.

Context: {context}

Return a JSON array of risk objects, each with:
- title: brief risk title
- description: detailed explanation of the risk
- severity: "high", "medium", or "low"
- category: "legal", "financial", "operational", or "compliance"
- mitigation: suggested mitigation strategy

Focus on:
- Unfavorable terms
- Liability issues
- Payment risks
- Termination risks
- IP ownership issues
- Confidentiality gaps
- Dispute resolution problems

Return ONLY valid JSON array, no additional text.
"""
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        docs = retriever.get_relevant_documents("risks liabilities termination payment") if hasattr(retriever, 'get_relevant_documents') else []
        content = format_docs(docs) if docs else ""
        
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm | self.output_parser
        
        result = chain.invoke({"context": content[:5000]})
        
        try:
            if result.strip().startswith('['):
                return json.loads(result)
            json_match = re.search(r'\[.*\]', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return []
    
    def _check_missing_clauses(self, retriever) -> List[Dict[str, str]]:
        """Check for missing important clauses"""
        template = """Check if this contract is missing any standard or important clauses.

Context: {context}

Return a JSON array of missing clauses, each with:
- clauseName: name of missing clause
- importance: "critical", "important", or "recommended"
- description: why this clause is needed
- suggestedWording: sample clause text (optional)

Check for:
- Termination clause
- Liability limitation
- Confidentiality/NDA
- Dispute resolution
- Force majeure
- IP ownership
- Payment terms
- Delivery/performance terms
- Warranties
- Indemnification

Return ONLY valid JSON array, no additional text.
"""
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        docs = retriever.get_relevant_documents("clauses terms conditions") if hasattr(retriever, 'get_relevant_documents') else []
        content = format_docs(docs) if docs else ""
        
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm | self.output_parser
        
        result = chain.invoke({"context": content[:5000]})
        
        try:
            if result.strip().startswith('['):
                return json.loads(result)
            json_match = re.search(r'\[.*\]', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return []
    
    def _identify_key_clauses(self, retriever) -> Dict[str, str]:
        """Identify and extract key clauses"""
        template = """Identify and extract key clauses from this contract.

Context: {context}

Return a JSON object with:
- payment: payment terms and schedule
- confidentiality: confidentiality/NDA terms
- liability: liability and limitation clauses
- termination: termination conditions
- ipOwnership: intellectual property ownership
- disputeResolution: dispute resolution mechanism
- warranties: warranty terms
- indemnification: indemnification clauses

For each clause, provide a brief summary (2-3 sentences).

Return ONLY valid JSON, no additional text.
"""
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        docs = retriever.get_relevant_documents("payment liability termination IP dispute") if hasattr(retriever, 'get_relevant_documents') else []
        content = format_docs(docs) if docs else ""
        
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm | self.output_parser
        
        result = chain.invoke({"context": content[:5000]})
        
        try:
            if result.strip().startswith('{'):
                return json.loads(result)
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return {}
    
    def _suggest_improvements(self, retriever, risks: List[Dict], missing_clauses: List[Dict]) -> List[Dict[str, str]]:
        """Suggest contract improvements"""
        template = """Based on the contract analysis, suggest specific improvements.

Context: {context}

Return a JSON array of improvements, each with:
- title: improvement title
- description: detailed explanation
- priority: "high", "medium", or "low"
- suggestedWording: recommended clause text or modification

Focus on:
- Addressing identified risks
- Adding missing clauses
- Clarifying ambiguous terms
- Strengthening weak protections
- Improving fairness

Return ONLY valid JSON array, no additional text.
"""
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        docs = retriever.get_relevant_documents("improvements recommendations") if hasattr(retriever, 'get_relevant_documents') else []
        content = format_docs(docs) if docs else ""
        
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm | self.output_parser
        
        result = chain.invoke({"context": content[:5000]})
        
        try:
            if result.strip().startswith('['):
                return json.loads(result)
            json_match = re.search(r'\[.*\]', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return []
    
    def _calculate_overall_risk(self, risks: List[Dict]) -> str:
        """Calculate overall risk level"""
        if not risks:
            return "low"
        
        high_count = sum(1 for r in risks if r.get("severity", "").lower() == "high")
        medium_count = sum(1 for r in risks if r.get("severity", "").lower() == "medium")
        
        if high_count >= 2:
            return "high"
        elif high_count >= 1 or medium_count >= 3:
            return "medium"
        else:
            return "low"

