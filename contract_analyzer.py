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

# No external dependencies - self-contained extraction


class ContractAnalyzer:
    """Professional contract analysis system"""
    
    def __init__(self, openai_api_key: str):
        from langchain_openai import ChatOpenAI
        # Use faster model with optimized settings for comprehensive analysis
        self.llm = ChatOpenAI(
            model="gpt-4o-mini", 
            temperature=0.1, 
            openai_api_key=openai_api_key,
            max_tokens=6000,  # Increased for comprehensive clause analysis
            timeout=90  # 90 second timeout for comprehensive analysis
        )
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
    
    def _extract_contract_content(self, retriever):
        """Extract contract content with multiple fallback strategies - self-contained"""
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        content = ""
        docs = []
        
        # Strategy 1: Search for contract-specific terms
        if hasattr(retriever, 'get_relevant_documents'):
            search_queries = [
                "contract agreement parties obligations terms conditions",
                "contract",
                "agreement",
                "parties obligations"
            ]
            for query in search_queries:
                try:
                    temp_docs = retriever.get_relevant_documents(query)
                    if temp_docs:
                        temp_content = format_docs(temp_docs)
                        if len(temp_content.strip()) > len(content.strip()):
                            content = temp_content
                            docs = temp_docs
                except:
                    continue
        
        # Strategy 2: Broader search
        if len(content.strip()) < 200:
            broad_queries = ["document", "text", "content", ""]
            for query in broad_queries:
                try:
                    if hasattr(retriever, 'get_relevant_documents'):
                        temp_docs = retriever.get_relevant_documents(query)
                        if temp_docs:
                            temp_content = format_docs(temp_docs)
                            if len(temp_content.strip()) > len(content.strip()):
                                content = temp_content
                                docs = temp_docs
                except:
                    continue
        
        # Strategy 3: Direct vectorstore access
        if len(content.strip()) < 200:
            try:
                vectorstore = None
                if hasattr(retriever, 'vectorstore'):
                    vectorstore = retriever.vectorstore
                elif hasattr(retriever, '_vectorstore'):
                    vectorstore = retriever._vectorstore
                
                if vectorstore:
                    try:
                        all_docs = vectorstore.similarity_search("", k=200)
                        if all_docs:
                            temp_content = format_docs(all_docs)
                            if len(temp_content.strip()) > len(content.strip()):
                                content = temp_content
                                docs = all_docs
                    except:
                        pass
            except:
                pass
        
        return content, docs
    
    def analyze_contract(self, retriever) -> Dict[str, Any]:
        """Comprehensive international contract analysis - globally neutral approach"""
        
        # Self-contained extraction
        content, docs = self._extract_contract_content(retriever)
        
        # Final check - be more lenient
        if not content or len(content.strip()) < 20:
            error_msg = "Could not extract sufficient content from the contract PDF. "
            error_msg += "Possible reasons: "
            error_msg += "1) The PDF might be image-based/scanned (requires OCR), "
            error_msg += "2) The PDF might be corrupted, "
            error_msg += "3) The PDF might not contain selectable text. "
            error_msg += "Please ensure the PDF contains selectable text or try converting it to a text-based PDF."
            print(f"ERROR: Contract extraction failed. Content length: {len(content) if content else 0} characters")
            print(f"Number of docs retrieved: {len(docs) if docs else 0}")
            return {
                "error": error_msg,
                "executiveSummary": [],
                "partiesAndType": {},
                "scopeAndObligations": {},
                "commercialTerms": {},
                "clauseAnalysis": [],
                "riskAssessment": [],
                "globalCompliance": {},
                "optionalImprovements": []
            }
        
        print(f"Contract content extracted: {len(content)} characters from {len(docs) if docs else 0} document chunks")
        
        # Comprehensive international contract analysis
        comprehensive_template = """You are a senior international contracts lawyer and enterprise project governance expert.

Analyze this contract WITHOUT assuming any country, governing law, or jurisdiction unless explicitly stated in the document.

Contract Document: {{context}}

Return a JSON object with the following structure:

1. executiveSummary: array of 5-6 bullet points covering: parties, contract type, scope, key commercial terms, main risks, overall assessment

2. partiesAndType: object with:
   - parties: object with provider/serviceProvider, client/customer (exact names from document)
   - contractType: type of contract (e.g., "Service Agreement", "Software License", "Consulting Agreement")
   - governingLaw: ONLY if explicitly stated in document, otherwise null
   - jurisdiction: ONLY if explicitly stated, otherwise null

3. scopeAndObligations: object with:
   - scopeOfServices: detailed description of services/deliverables
   - providerObligations: array of obligations (each with title, description, deadline if any)
   - clientObligations: array of obligations (each with title, description, deadline if any)

4. commercialTerms: object with:
   - pricing: pricing structure and amounts
   - paymentTerms: payment schedule, milestones, invoicing requirements
   - currency: currency if specified
   - paymentMethod: payment method if specified

5. clauseAnalysis: array of clause objects, each with:
   - clauseName: one of: "Scope & Deliverables", "Payment & Invoicing", "Confidentiality", "Intellectual Property", "Data Protection & Privacy", "Service Levels / Support", "Warranties & Disclaimers", "Indemnification", "Limitation of Liability", "Term & Termination", "Force Majeure", "Change Management", "Dispute Resolution", "Governing Law"
   - presence: "present", "weak", or "missing"
   - adequacy: "adequate", "weak", or "missing" (only if present)
   - balance: "balanced", "favorable to provider", "favorable to client", or "unclear"
   - summary: 2-3 sentence summary of what the clause says (or why it's missing/weak)
   - assessment: brief assessment of strengths and weaknesses

6. riskAssessment: array of risk objects, each with:
   - title: brief risk title
   - description: detailed explanation of why this risk exists
   - riskLevel: "LOW", "MEDIUM", or "HIGH"
   - category: "legal", "financial", "operational", "compliance", or "commercial"
   - affectedClause: which clause(s) this risk relates to
   - impact: potential impact if risk materializes
   - recommendation: suggested mitigation

7. globalCompliance: object with:
   - dataPrivacyGaps: array of gaps related to data privacy (GDPR, CCPA, etc.)
   - crossBorderIssues: array of issues related to cross-border delivery/enforcement
   - internationalEnforceability: assessment of enforceability across jurisdictions
   - complianceRecommendations: array of recommendations for global compliance

8. optionalImprovements: array of improvement objects, each with:
   - title: improvement title
   - clauseName: which clause this relates to
   - description: why this improvement is recommended
   - suggestedWording: optional, jurisdiction-agnostic clause wording
   - priority: "high", "medium", or "low"
   - note: "OPTIONAL - This is a suggested improvement, not a requirement"

IMPORTANT RULES:
- Do NOT assume any country or jurisdiction unless explicitly stated
- Do NOT inject country-specific laws
- Mark clauses as "weak" if they exist but are brief, NOT "missing"
- Use internationally accepted commercial contract language
- Keep all suggestions neutral and globally applicable
- Do NOT rewrite the contract, only analyze and suggest

Return ONLY valid JSON, no additional text.
"""
        
        # Replace double braces with single for context variable
        formatted_template = comprehensive_template.replace("{{context}}", "{context}")
        prompt = PromptTemplate.from_template(formatted_template)
        chain = prompt | self.llm | self.output_parser
        
        try:
            # Use larger context window for comprehensive analysis
            result = chain.invoke({"context": content[:15000]})  # Increased for comprehensive international analysis
            
            # Parse the comprehensive result
            if result.strip().startswith('{'):
                analysis = json.loads(result)
            else:
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                else:
                    analysis = {}
            
            # Extract all fields with defaults
            return {
                "executiveSummary": analysis.get("executiveSummary", []),
                "partiesAndType": analysis.get("partiesAndType", {
                    "parties": {"provider": "Unknown", "client": "Unknown"},
                    "contractType": "Contract",
                    "governingLaw": None,
                    "jurisdiction": None
                }),
                "scopeAndObligations": analysis.get("scopeAndObligations", {
                    "scopeOfServices": "",
                    "providerObligations": [],
                    "clientObligations": []
                }),
                "commercialTerms": analysis.get("commercialTerms", {
                    "pricing": "",
                    "paymentTerms": "",
                    "currency": None,
                    "paymentMethod": None
                }),
                "clauseAnalysis": analysis.get("clauseAnalysis", []),
                "riskAssessment": analysis.get("riskAssessment", []),
                "globalCompliance": analysis.get("globalCompliance", {
                    "dataPrivacyGaps": [],
                    "crossBorderIssues": [],
                    "internationalEnforceability": "",
                    "complianceRecommendations": []
                }),
                "optionalImprovements": analysis.get("optionalImprovements", []),
                "overallRiskLevel": self._calculate_overall_risk(analysis.get("riskAssessment", []))
            }
        except Exception as e:
            print(f"Error in comprehensive contract analysis: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to basic analysis
            return {
                "error": f"Error analyzing contract: {str(e)}. Please try again.",
                "executiveSummary": [],
                "partiesAndType": {"parties": {"provider": "Unknown", "client": "Unknown"}},
                "scopeAndObligations": {"scopeOfServices": "", "providerObligations": [], "clientObligations": []},
                "commercialTerms": {},
                "clauseAnalysis": [],
                "riskAssessment": [],
                "globalCompliance": {},
                "optionalImprovements": [],
                "overallRiskLevel": "LOW"
            }
    
    def _extract_metadata(self, retriever) -> Dict[str, Any]:
        """Extract contract metadata: parties, dates, value, etc."""
        template = """Extract key metadata from this contract document.

Context: {context}

Return a JSON object with:
- parties: {{"provider": "name", "client": "name"}}
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
            return "LOW"
        
        high_count = sum(1 for r in risks if r.get("riskLevel", "").upper() == "HIGH")
        medium_count = sum(1 for r in risks if r.get("riskLevel", "").upper() == "MEDIUM")
        
        if high_count >= 2:
            return "HIGH"
        elif high_count >= 1 or medium_count >= 3:
            return "MEDIUM"
        else:
            return "LOW"

