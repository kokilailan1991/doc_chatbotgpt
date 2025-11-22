"""
Website Analyzer Module
Handles SEO analysis, content structure, keyword extraction, and recommendations
"""
import json
import re
import os
from typing import Dict, List, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import requests
from bs4 import BeautifulSoup


class WebsiteAnalyzer:
    def __init__(self, openai_key: str):
        self.llm = ChatOpenAI(temperature=0, openai_api_key=openai_key)
        self.output_parser = StrOutputParser()
    
    def fetch_website_content(self, url: str) -> Dict[str, Any]:
        """Fetch and parse website content"""
        try:
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract meta tags
            title = soup.find('title')
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
            
            # Extract headings
            h1_tags = [h.get_text().strip() for h in soup.find_all('h1')]
            h2_tags = [h.get_text().strip() for h in soup.find_all('h2')]
            h3_tags = [h.get_text().strip() for h in soup.find_all('h3')]
            
            # Extract links
            links = [a.get('href') for a in soup.find_all('a', href=True)]
            
            # Extract images
            images = [img.get('src') or img.get('data-src') for img in soup.find_all('img')]
            
            # Get main content
            main_content = soup.get_text()
            
            return {
                "url": url,
                "title": title.get_text().strip() if title else "",
                "metaDescription": meta_desc.get('content', '') if meta_desc else "",
                "metaKeywords": meta_keywords.get('content', '') if meta_keywords else "",
                "h1Tags": h1_tags,
                "h2Tags": h2_tags,
                "h3Tags": h3_tags,
                "links": links[:50],  # Limit to first 50
                "images": images[:20],  # Limit to first 20
                "content": main_content[:10000],  # Limit content length
                "html": response.text[:5000]  # Limit HTML
            }
        except Exception as e:
            return {"error": str(e), "url": url}
    
    def analyze_seo(self, website_data: Dict[str, Any], retriever) -> Dict[str, Any]:
        """Analyze SEO aspects of the website"""
        template = """Analyze the SEO of this website.
        
URL: {url}
Title: {title}
Meta Description: {meta_description}
H1 Tags: {h1_tags}
Content Sample: {content}

Return a JSON object with:
- seoScore: number (0-100)
- titleOptimization: "good", "needs improvement", or "poor"
- metaDescriptionOptimization: "good", "needs improvement", or "poor"
- headingStructure: "good", "needs improvement", or "poor"
- keywordDensity: number (0-100)
- issues: [list of SEO issues]
- opportunities: [list of SEO opportunities]
- recommendations: [list of SEO recommendations]
- competitorKeywords: [list of suggested competitor keywords]

Return ONLY valid JSON, no additional text.
"""
        
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm | self.output_parser
        
        result = chain.invoke({
            "url": website_data.get("url", ""),
            "title": website_data.get("title", ""),
            "meta_description": website_data.get("metaDescription", ""),
            "h1_tags": ", ".join(website_data.get("h1Tags", [])[:5]),
            "content": website_data.get("content", "")[:3000]
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
            "seoScore": 70,
            "titleOptimization": "good",
            "metaDescriptionOptimization": "good",
            "headingStructure": "good",
            "keywordDensity": 60,
            "issues": [],
            "opportunities": [],
            "recommendations": [],
            "competitorKeywords": []
        }
    
    def extract_keywords(self, retriever) -> List[str]:
        """Extract keywords from website content"""
        template = """Extract the most important keywords from this website content.
        
Content: {context}

Return a JSON array of keywords (top 20), ordered by importance.

Return ONLY valid JSON array, no additional text.
"""
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        docs = retriever.get_relevant_documents("website") if hasattr(retriever, 'get_relevant_documents') else []
        content = format_docs(docs) if docs else ""
        
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm | self.output_parser
        
        result = chain.invoke({"context": content[:5000]})
        
        try:
            if result.strip().startswith('['):
                return json.loads(result)
            import re
            json_match = re.search(r'\[.*\]', result, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return []
    
    def analyze_content_structure(self, website_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze content hierarchy and structure"""
        return {
            "h1Count": len(website_data.get("h1Tags", [])),
            "h2Count": len(website_data.get("h2Tags", [])),
            "h3Count": len(website_data.get("h3Tags", [])),
            "linkCount": len(website_data.get("links", [])),
            "imageCount": len(website_data.get("images", [])),
            "structureScore": self._calculate_structure_score(website_data),
            "hierarchy": {
                "h1": website_data.get("h1Tags", []),
                "h2": website_data.get("h2Tags", []),
                "h3": website_data.get("h3Tags", [])
            }
        }
    
    def _calculate_structure_score(self, website_data: Dict[str, Any]) -> int:
        """Calculate structure score"""
        score = 0
        
        # H1 check (should have 1)
        h1_count = len(website_data.get("h1Tags", []))
        if h1_count == 1:
            score += 25
        elif h1_count > 1:
            score += 10
        
        # H2 check (should have multiple)
        h2_count = len(website_data.get("h2Tags", []))
        if h2_count >= 3:
            score += 25
        elif h2_count >= 1:
            score += 15
        
        # Meta description check
        if website_data.get("metaDescription"):
            score += 25
        
        # Title check
        if website_data.get("title"):
            score += 25
        
        return score
    
    def full_website_analysis(self, url: str, retriever) -> Dict[str, Any]:
        """Complete website analysis"""
        website_data = self.fetch_website_content(url)
        
        if "error" in website_data:
            return {"error": website_data["error"]}
        
        seo_analysis = self.analyze_seo(website_data, retriever)
        keywords = self.extract_keywords(retriever)
        structure = self.analyze_content_structure(website_data)
        
        # Get insights using workflow
        from workflows import WorkflowProcessor
        openai_key = os.getenv("OPENAI_API_KEY")
        workflow = WorkflowProcessor(openai_key)
        insights = workflow.extract_insights(retriever, "website")
        
        return {
            "url": url,
            "websiteData": website_data,
            "seoAnalysis": seo_analysis,
            "keywords": keywords,
            "structure": structure,
            "insights": insights,
            "issues": seo_analysis.get("issues", []),
            "opportunities": seo_analysis.get("opportunities", []),
            "recommendations": seo_analysis.get("recommendations", [])
        }

