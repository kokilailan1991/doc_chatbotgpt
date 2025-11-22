"""
Output Format Generators
Handles JSON, Excel, PDF, Email, Slack/Teams outputs
"""
import json
import csv
import io
from typing import Dict, List, Any
from datetime import datetime


class OutputGenerator:
    @staticmethod
    def to_json(data: Any, indent: int = 2) -> str:
        """Convert data to JSON string"""
        return json.dumps(data, indent=indent, default=str)
    
    @staticmethod
    def to_excel_csv(data: List[Dict[str, Any]], filename: str = "export") -> str:
        """Convert data to CSV format (Excel compatible)"""
        if not data:
            return ""
        
        output = io.StringIO()
        fieldnames = data[0].keys() if isinstance(data[0], dict) else []
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in data:
            if isinstance(row, dict):
                writer.writerow(row)
            else:
                writer.writerow({"value": str(row)})
        
        return output.getvalue()
    
    @staticmethod
    def to_email_draft(subject: str, body: str, recipients: List[str] = None) -> Dict[str, Any]:
        """Generate email draft"""
        return {
            "subject": subject,
            "body": body,
            "recipients": recipients or [],
            "cc": [],
            "bcc": [],
            "format": "html"
        }
    
    @staticmethod
    def to_slack_message(title: str, content: str, fields: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """Generate Slack message format"""
        return {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": title
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": content
                    }
                }
            ]
        }
    
    @staticmethod
    def to_teams_message(title: str, content: str, facts: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """Generate Teams message format"""
        return {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": title,
            "themeColor": "0078D4",
            "title": title,
            "text": content,
            "sections": [
                {
                    "facts": facts or []
                }
            ]
        }
    
    @staticmethod
    def generate_pdf_content(data: Dict[str, Any], title: str = "Document Analysis") -> str:
        """Generate PDF content (HTML format for conversion)"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #6C5DD3; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #6C5DD3; color: white; }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """
        
        # Add content based on data structure
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, list):
                    html += f"<h2>{key}</h2><ul>"
                    for item in value:
                        html += f"<li>{item}</li>"
                    html += "</ul>"
                else:
                    html += f"<p><strong>{key}:</strong> {value}</p>"
        
        html += """
        </body>
        </html>
        """
        return html

