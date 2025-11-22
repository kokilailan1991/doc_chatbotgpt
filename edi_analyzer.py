"""
Logistics/EDI Analyzer Module
Handles BAPLIE, MOVINS, COPRAR, and other EDI format validation
"""
import json
import re
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


class EDIAnalyzer:
    def __init__(self, openai_key: str):
        self.llm = ChatOpenAI(temperature=0, openai_api_key=openai_key)
        self.output_parser = StrOutputParser()
    
    def detect_edi_format(self, content: str) -> str:
        """Detect EDI format type"""
        content_upper = content.upper()
        
        if 'BAPLIE' in content_upper or 'BGM+945' in content_upper:
            return "BAPLIE"
        elif 'MOVINS' in content_upper or 'BGM+910' in content_upper:
            return "MOVINS"
        elif 'COPRAR' in content_upper or 'BGM+920' in content_upper:
            return "COPRAR"
        elif 'UNB' in content_upper and 'UNH' in content_upper:
            return "EDIFACT"
        elif 'ISA' in content_upper and 'GS' in content_upper:
            return "X12"
        else:
            return "UNKNOWN"
    
    def validate_structure(self, content: str, format_type: str) -> Dict[str, Any]:
        """Validate EDI structure"""
        errors = []
        warnings = []
        
        if format_type == "BAPLIE":
            if 'BGM+945' not in content.upper():
                errors.append("Missing BGM segment (Message Header)")
            if 'TDT+' not in content.upper():
                warnings.append("Missing TDT segment (Transport Details)")
            if 'LOC+' not in content.upper():
                warnings.append("Missing LOC segment (Location)")
        
        elif format_type == "MOVINS":
            if 'BGM+910' not in content.upper():
                errors.append("Missing BGM segment (Message Header)")
            if 'TDT+' not in content.upper():
                warnings.append("Missing TDT segment (Transport Details)")
        
        elif format_type == "COPRAR":
            if 'BGM+920' not in content.upper():
                errors.append("Missing BGM segment (Message Header)")
        
        # Check for basic EDI structure
        if format_type in ["EDIFACT", "BAPLIE", "MOVINS", "COPRAR"]:
            if "'" not in content and "+" not in content:
                errors.append("Invalid EDI format - missing segment separators")
        
        return {
            "isValid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "formatType": format_type
        }
    
    def analyze_edi(self, retriever) -> Dict[str, Any]:
        """Analyze EDI document"""
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        docs = retriever.get_relevant_documents("EDI document") if hasattr(retriever, 'get_relevant_documents') else []
        content = format_docs(docs) if docs else ""
        format_type = self.detect_edi_format(content)
        validation = self.validate_structure(content, format_type)
        
        template = """Analyze this EDI document and extract key information.
        
EDI Format: {format_type}
Content: {context}

Extract and return a JSON object with:
- summary: brief summary of the EDI message
- keyFields: [list of key fields and their values]
- parties: [list of parties involved]
- locations: [list of locations]
- dates: [list of important dates]
- quantities: [list of quantities]
- errors: [list of data errors found]
- warnings: [list of warnings]

Return ONLY valid JSON, no additional text.
"""
        
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm | self.output_parser
        
        result = chain.invoke({
            "format_type": format_type,
            "context": content[:5000]  # Limit content length
        })
        
        try:
            if result.strip().startswith('{'):
                analysis = json.loads(result)
            else:
                import re
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                else:
                    analysis = {}
        except:
            analysis = {}
        
        # Merge validation results
        analysis["validation"] = validation
        analysis["formatType"] = format_type
        
        return analysis
    
    def generate_json_output(self, analysis: Dict[str, Any]) -> str:
        """Generate JSON output for EDI analysis"""
        return json.dumps(analysis, indent=2)
    
    def generate_table_output(self, analysis: Dict[str, Any]) -> List[List[str]]:
        """Generate table output for EDI analysis"""
        table = []
        
        # Header
        table.append(["Field", "Value"])
        
        # Key fields
        if "keyFields" in analysis:
            for field in analysis["keyFields"]:
                if isinstance(field, dict):
                    table.append([field.get("name", ""), field.get("value", "")])
                else:
                    table.append([str(field), ""])
        
        # Parties
        if "parties" in analysis:
            for party in analysis["parties"]:
                table.append(["Party", str(party)])
        
        # Locations
        if "locations" in analysis:
            for location in analysis["locations"]:
                table.append(["Location", str(location)])
        
        return table

