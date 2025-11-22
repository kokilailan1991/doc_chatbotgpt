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
        """Detect EDI format type - Enhanced with more formats"""
        content_upper = content.upper()
        
        if 'BAPLIE' in content_upper or 'BGM+945' in content_upper:
            return "BAPLIE"
        elif 'MOVINS' in content_upper or 'BGM+910' in content_upper:
            return "MOVINS"
        elif 'COPRAR' in content_upper or 'BGM+920' in content_upper:
            return "COPRAR"
        elif 'IFTMIN' in content_upper or 'BGM+380' in content_upper:
            return "IFTMIN"
        elif 'CODECO' in content_upper or 'BGM+950' in content_upper:
            return "CODECO"
        elif 'CUSCAR' in content_upper or 'BGM+951' in content_upper:
            return "CUSCAR"
        elif 'UNB' in content_upper and 'UNH' in content_upper:
            return "EDIFACT"
        elif 'ISA' in content_upper and 'GS' in content_upper:
            return "X12"
        else:
            return "UNKNOWN"
    
    def validate_structure(self, content: str, format_type: str) -> Dict[str, Any]:
        """Validate EDI structure with comprehensive rules"""
        errors = []
        warnings = []
        suggestions = []
        
        content_upper = content.upper()
        
        # Container number validation regex
        container_pattern = r'[A-Z]{4}[0-9]{7}'
        containers_found = []
        
        if format_type == "BAPLIE":
            if 'BGM+945' not in content_upper:
                errors.append("Missing BGM segment (Message Header) - Required for BAPLIE")
            if 'TDT+' not in content_upper:
                warnings.append("Missing TDT segment (Transport Details)")
            if 'LOC+' not in content_upper:
                errors.append("Missing LOC segment (Location) - Required for container stowage")
            if 'EQD+' not in content_upper:
                errors.append("Missing EQD segment (Equipment Details) - Required for container info")
            
            # Check for container numbers
            import re
            containers = re.findall(container_pattern, content)
            if not containers:
                warnings.append("No valid container numbers found (format: ABCD1234567)")
            else:
                containers_found = list(set(containers))
                # Check for duplicates
                if len(containers) != len(containers_found):
                    errors.append(f"Duplicate container records found: {len(containers) - len(containers_found)} duplicates")
            
            # Check for stowage positions
            if 'LOC+147' not in content_upper and 'LOC+9' not in content_upper:
                warnings.append("Missing stowage position information (LOC segments)")
            
            # Check for weight mismatches (basic check)
            if 'MEA+AAE' in content_upper or 'MEA+WT' in content_upper:
                # Weight information present
                pass
            else:
                warnings.append("Missing weight information (MEA segments)")
        
        elif format_type == "MOVINS":
            if 'BGM+910' not in content_upper:
                errors.append("Missing BGM segment (Message Header)")
            if 'TDT+' not in content_upper:
                warnings.append("Missing TDT segment (Transport Details)")
            if 'NAD+' not in content_upper:
                warnings.append("Missing NAD segment (Name and Address)")
            if 'RFF+' not in content_upper:
                warnings.append("Missing RFF segment (Reference)")
        
        elif format_type == "COPRAR":
            if 'BGM+920' not in content_upper:
                errors.append("Missing BGM segment (Message Header)")
            if 'NAD+' not in content_upper:
                warnings.append("Missing NAD segment (Name and Address)")
        
        elif format_type == "IFTMIN":
            if 'BGM+380' not in content_upper:
                errors.append("Missing BGM segment (Message Header)")
            if 'TDT+' not in content_upper:
                warnings.append("Missing TDT segment (Transport Details)")
        
        elif format_type == "CODECO":
            if 'BGM+950' not in content_upper:
                errors.append("Missing BGM segment (Message Header)")
            if 'CNT+' not in content_upper:
                warnings.append("Missing CNT segment (Container Count)")
        
        elif format_type == "CUSCAR":
            if 'BGM+951' not in content_upper:
                errors.append("Missing BGM segment (Message Header)")
            if 'CUS+' not in content_upper:
                warnings.append("Missing CUS segment (Customs Information)")
        
        # Check for basic EDI structure
        if format_type in ["EDIFACT", "BAPLIE", "MOVINS", "COPRAR"]:
            if "'" not in content and "+" not in content:
                errors.append("Invalid EDI format - missing segment separators (' or +)")
            else:
                # Check segment count
                segments = content.split("'")
                if len(segments) < 5:
                    warnings.append(f"Low segment count ({len(segments)} segments) - file may be incomplete")
        
        # Generate suggestions
        if errors:
            suggestions.append("Review EDI structure and ensure all required segments are present")
        if warnings:
            suggestions.append("Consider adding missing optional segments for better data completeness")
        if containers_found and len(containers_found) > 0:
            suggestions.append(f"Found {len(containers_found)} unique containers - verify container numbers match physical containers")
        
        return {
            "isValid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions,
            "formatType": format_type,
            "containersFound": len(containers_found),
            "containerNumbers": containers_found[:10]  # First 10 for preview
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
- summary: brief summary of the EDI message (2-3 sentences)
- keyFields: [list of key fields and their values as objects with "name" and "value"]
- parties: [list of parties involved with roles]
- locations: [list of locations with types (origin, destination, etc.)]
- dates: [list of important dates with descriptions]
- quantities: [list of quantities with units]
- containers: [list of container numbers and their details]
- errors: [list of data errors found beyond structure validation]
- warnings: [list of warnings beyond structure validation]

Return ONLY valid JSON, no additional text.
"""
        
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm | self.output_parser
        
        result = chain.invoke({
            "format_type": format_type,
            "context": content[:8000]  # Increased limit for better analysis
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
        except Exception as e:
            print(f"Error parsing EDI analysis: {e}")
            analysis = {}
        
        # Merge validation results and enhance
        analysis["validation"] = validation
        analysis["formatType"] = format_type
        analysis["errors"] = validation.get("errors", []) + analysis.get("errors", [])
        analysis["warnings"] = validation.get("warnings", []) + analysis.get("warnings", [])
        analysis["suggestions"] = validation.get("suggestions", [])
        
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

